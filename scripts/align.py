#!/usr/bin/env python3
"""align.py <transcript> <metrics.json> [out_prefix]"""
import sys, json, csv, re, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config
CFG = load_config(); B = CFG["benchmarks"]
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
exp, ent = H.get("exposure"), H.get("entries")
def judge(x, rng, unit, low="偏低", high="偏高"):
    lo, hi = rng
    return f"正常({lo}–{hi}{unit})" if lo <= x <= hi else (f"{low}(<{lo}{unit})" if x < lo else f"{high}(>{hi}{unit})")
if B.get("cpl_range") and sp is not None:
    if ld: v["线索成本"] = f"{sp / ld:.2f} 元 → " + judge(sp / ld, B["cpl_range"], "元", "偏低，好", "超标")
    else: v["线索成本"] = "0 线索 → 超标"
if B.get("entry_rate_range") and exp and ent is not None:
    rate = ent / exp * 100; v["曝光进入率"] = f"{rate:.2f}% → " + judge(rate, B["entry_rate_range"], "%")
aw = H.get("avg_watch_s")
if B.get("avg_watch_range") and aw is not None:
    ab = B.get("avg_watch_abnormal_above")
    v["人均停留"] = f"{aw}s → " + (f"异常(>{ab}s，查闲聊/人少)" if ab is not None and aw > ab else judge(aw, B["avg_watch_range"], "s", "偏短", "略高"))
v["_基准来源"] = "LR_CONFIG 配置" if os.environ.get("LR_CONFIG") else "内置示例参考值（请填写自己的基准）"
car = (M.get("car") or "").upper()
tgt = next((a for k, a in CFG["target_ages"].items() if k.upper() in car), None)
if tgt: v["目标年龄"] = f"{car} 目标 {tgt} 岁；实际年龄分布：{H.get('age_dist', '待填')}"
if ent:
    clk = H.get("card_clicks", 0) + H.get("windmill_clicks", 0)
    v["漏斗"] = f"曝光{exp} → 进入{ent} → 卡片{H.get('card_clicks',0)}/风车{H.get('windmill_clicks',0)} → 线索{ld}"
json.dump({"verdicts": v, "flag_rows": [r for r in rows if r["flags"]]}, open(prefix + "_verdicts.json", "w"), ensure_ascii=False, indent=1)
for k, x in v.items(): print(f"{k}: {x}")
