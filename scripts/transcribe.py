#!/usr/bin/env python3
"""transcribe.py <ts_file> <start_beijing HH:MM:SS> <date YYYY-MM-DD> <out_prefix>"""
import sys, os, subprocess, datetime, json
import numpy as np
from faster_whisper import WhisperModel
from opencc import OpenCC
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config
CFG = load_config()
FIXES = CFG["asr_fixes"]
MODEL = os.environ.get("LR_MODEL", "medium")
PROMPT = os.environ.get("LR_PROMPT", CFG["asr_prompt"])
THREADS = int(os.environ.get("LR_THREADS", os.cpu_count() or 4))

def main():
    ts, start, date, prefix = sys.argv[1:5]
    os.makedirs(os.path.dirname(os.path.abspath(prefix)), exist_ok=True)
    t0 = datetime.datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M:%S")
    wav = prefix + ".wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ts, "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", wav], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ts], capture_output=True, text=True).stdout.strip() or 0)
    # frames
    fdir = prefix + "_frames"; os.makedirs(fdir, exist_ok=True)
    for i in range(6):
        t = dur * (i + 0.5) / 6
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.1f}", "-i", ts, "-frames:v", "1", "-q:v", "3",
                        f"{fdir}/{(t0+datetime.timedelta(seconds=t)).strftime('%H%M%S')}.jpg"])
    audio = np.frombuffer(open(wav, "rb").read()[44:], dtype=np.int16).astype(np.float32) / 32768
    m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=THREADS)
    segs, _ = m.transcribe(audio, language="zh", vad_filter=True, beam_size=1, condition_on_previous_text=False, initial_prompt=PROMPT)
    cc = OpenCC("t2s"); rows = []
    for s in segs:
        txt = cc.convert(s.text.strip())
        for a, b in FIXES.items(): txt = txt.replace(a, b)
        rows.append((s.start, s.end, txt))
    bj = lambda sec: (t0 + datetime.timedelta(seconds=sec)).strftime("%H:%M:%S")
    with open(prefix + "_transcript.txt", "w") as f:
        for a, b, t in rows: f.write(f"{bj(a)} {t}\n")
    # silence gaps > 30s
    gaps, prev = [], 0.0
    for a, b, _ in rows + [(dur, dur, "")]:
        if a - prev > 30: gaps.append((bj(prev), bj(a), round(a - prev)))
        prev = max(prev, b)
    with open(prefix + "_gaps.txt", "w") as f:
        f.write("\n".join(f"{a}-{b} 静音{s}s" for a, b, s in gaps) or "无超过30秒的空档")
        f.write("\n")
    json.dump({"segments": len(rows), "duration_s": dur, "gaps": gaps}, open(prefix + "_meta.json", "w"), ensure_ascii=False)
    if os.environ.get("LR_KEEP_TS") != "1": os.remove(ts)
    os.remove(wav)
    print(f"OK {len(rows)} segments, {len(gaps)} gaps -> {prefix}_transcript.txt")
if __name__ == "__main__":
    if len(sys.argv) < 5: sys.exit(__doc__)
    main()
