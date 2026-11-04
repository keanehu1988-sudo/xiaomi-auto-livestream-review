#!/bin/bash
# run_day.sh <YYYY-MM-DD>   inbox/<date>/<name>.json + <name>.ts
set -u
D=${1:?usage: run_day.sh YYYY-MM-DD}
SCRIPTS=$(cd "$(dirname "$0")" && pwd)
BASE=${LR_BASE:-$PWD}; IN=${LR_INBOX:-$BASE/inbox}/$D; OUT=${LR_OUT:-$BASE/out}/$D; PY=${LR_PYTHON:-python3}
mkdir -p "$OUT"; S=$OUT/summary.md
echo "# $D 直播大屏复盘汇总（北京时间）" > "$S"; echo >> "$S"
for J in "$IN"/*.json; do
  [ -e "$J" ] || { echo "no metrics in $IN"; exit 1; }
  N=$(basename "$J" .json); TS="$IN/$N.ts"; P="$OUT/$N"
  START=$($PY -c "import json;print(json.load(open('$J'))['start_beijing'])")
  if [ -f "$TS" ]; then $PY "$SCRIPTS/transcribe.py" "$TS" "$START" "$D" "$P" || { echo "transcribe failed: $N"; continue; }
  elif [ ! -f "${P}_transcript.txt" ]; then echo "skip $N: no .ts and no transcript"; continue; fi
  $PY "$SCRIPTS/align.py" "${P}_transcript.txt" "$J" "$P" > "${P}_verdicts.txt"
  $PY - "$J" "$P" >> "$S" <<'PYEOF'
import json,sys
M=json.load(open(sys.argv[1]));H=M.get("headline",{});V=json.load(open(sys.argv[2]+"_verdicts.json"))
print(f"## {M.get('start_beijing','')[:5]}–{M.get('end_beijing','')[:5]} {M.get('anchor','')} · {M.get('car','')}\n")
print(f"- 得分：__\n- 消耗 {H.get('spend')} 元 / 线索 {H.get('leads')} 条（{', '.join(M.get('lead_times',[]))}）")
for k,x in V["verdicts"].items(): print(f"- {k}：{x}")
print(f"- 空档：{open(sys.argv[2]+'_gaps.txt').read().strip()}" if __import__('os').path.exists(sys.argv[2]+'_gaps.txt') else "")
print(f"- 对齐表：{sys.argv[2]}_align.md\n\n### 有效话术\n- \n\n### 掉人/无效话术\n- \n\n### 画面\n- \n\n### 优化建议\n1. \n")
PYEOF
done
printf "## 全天对比与明日重点\n\n" >> "$S"; echo "done -> $S"
