#!/usr/bin/env python3
"""align.py <transcript> <metrics.json> [out_prefix]"""
import sys, json, csv, re, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config
CFG = load_config(); LO, HI = CFG["cpl_range"]
if len(sys.argv) < 3: sys.exit(__doc__)
tr, mj = sys.argv[1:3]
prefix = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(tr)[0].replace("_transcript", "")
M = json.load(open(mj)); H = M.get("headline", {})
lines = []
for l in open(tr):
    m = re.match(r"(\d\d):(\d\d):(\d\d) (.*)", l.strip())
    if m: lines.append((int(m[1]) * 60 + int(m[2]), m[4]))
def mins(hm): h, m = map(int, hm.split(":")[:2]); return h * 60 + m
ser = M.get("per_minute", [])
leadmins = {t[:5] for t in M.get("lead_times", [])}
def peak(key, q=0.85):
    v = sorted(r.get(key, 0) for r in ser)
    if not v or v[-1] <= 0: return None
    p, med = v[int(len(v) * q)], v[len(v) // 2]
    return p if p > med else med + 1
pe, pc, pw = peak("entries"), peak("card_clicks"), peak("windmill_clicks")
rows = []
for r in ser:
    t = mins(r["time"]); flags = []
    if r["time"][:5] in leadmins or r.get("leads", 0) > 0: flags.append("线索")
    if pc and r.get("card_clicks", 0) >= max(pc, 1): flags.append("卡片点击高峰")
    if pw and r.get("windmill_clicks", 0) >= max(pw, 1): flags.append("小风车高峰")
    if pe and r.get("entries", 0) >= max(pe, 1): flags.append("进入高峰")
    if r.get("online", 1) == 0: flags.append("在线为0")
    speech = " / ".join(s for m, s in lines if t - 2 <= m <= t - 1)
    rows.append({**{k: r.get(k, "") for k in ["time", "entries", "online", "leads", "card_clicks", "windmill_clicks"]},
                 "flags": ",".join(flags), "speech_t-2~t-1": speech})
cols = ["time", "entries", "online", "leads", "card_clicks", "windmill_clicks", "flags", "speech_t-2~t-1"]
with open(prefix + "_align.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
with open(prefix + "_align.md", "w") as f:
    f.write("| 时间 | 进入 | 在线 | 线索 | 卡片 | 风车 | 标记 | 前1–2分钟话术 |\n|" + "---|" * 8 + "\n")
    for r in rows: f.write("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |\n")
# verdicts
v = {}
sp, ld = H.get("spend"), H.get("leads")
if sp is not None and ld:
    cpl = sp / ld; v["线索成本"] = f"{cpl:.2f} 元 → " + (f"正常({LO}–{HI})" if LO <= cpl <= HI else (f"偏低(<{LO}，好)" if cpl < LO else f"超标(>{HI})"))
elif sp is not None: v["线索成本"] = "0 线索 → 超标"
exp, ent = H.get("exposure"), H.get("entries")
if exp and ent is not None:
    rate = ent / exp * 100; v["曝光进入率"] = f"{rate:.2f}% → " + ("正常(5–15%)" if 5 <= rate <= 15 else ("偏低" if rate < 5 else "偏高"))
aw = H.get("avg_watch_s")
if aw is not None:
    v["人均停留"] = f"{aw}s → " + ("正常(10–15s)" if 10 <= aw <= 15 else ("异常(>25s，查闲聊/人少)" if aw > 25 else ("偏短(<10s)" if aw < 10 else "略高(15–25s)")))
car = (M.get("car") or "").upper()
tgt = next((a for k, a in CFG["target_ages"].items() if k.upper() in car), None)
if tgt: v["目标年龄"] = f"{car} 目标 {tgt} 岁；实际年龄分布：{H.get('age_dist', '待填')}"
if ent:
    clk = H.get("card_clicks", 0) + H.get("windmill_clicks", 0)
    v["漏斗"] = f"曝光{exp} → 进入{ent} → 卡片{H.get('card_clicks',0)}/风车{H.get('windmill_clicks',0)} → 线索{ld}"
json.dump({"verdicts": v, "flag_rows": [r for r in rows if r["flags"]]}, open(prefix + "_verdicts.json", "w"), ensure_ascii=False, indent=1)
for k, x in v.items(): print(f"{k}: {x}")
