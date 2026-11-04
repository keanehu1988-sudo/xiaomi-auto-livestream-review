# car-livestream-review · 汽车直播间直播大屏复盘

一个用于汽车经销商抖音付费投流直播间复盘的 Skill + 脚本工具集：读巨懂车/巨量直播大屏的流量漏斗与趋势曲线，下载回放并转写话术，把话术和关键分钟对齐，找出带来留资的话术和掉人的话术，按标准判定、打分并给出优化建议。

- `SKILL.md`：给 AI 助手用的复盘方法（判断标准 + 步骤）
- `scripts/transcribe.py`：回放转写（faster-whisper + opencc），截帧，找 >30 秒空档
- `scripts/align.py`：话术与每分钟数据对齐，自动标记关键分钟并给出判定
- `scripts/run_day.sh`：批量处理一天所有场次，生成 `summary.md` 骨架

> 读大屏数据（登录、悬停曲线）需要人或 AI 助手在浏览器里完成，本仓库脚本不包含任何登录或抓取逻辑。

## 安装
```bash
# 系统依赖
sudo apt install ffmpeg        # macOS: brew install ffmpeg
# Python 依赖（建议虚拟环境）
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # faster-whisper, opencc, numpy
```
首次运行会自动下载 Whisper 模型（默认 `medium`）。

## 用法
```bash
# 目录约定：inbox/<日期>/<场次名>.json + <场次名>.ts（同名一对）
LR_PYTHON=.venv/bin/python scripts/run_day.sh 2026-01-01   # 输出到 out/<日期>/

# 单独使用
scripts/transcribe.py 回放.ts 19:30:00 2026-01-01 out/2026-01-01/s1930
scripts/align.py out/2026-01-01/s1930_transcript.txt example_metrics.json
```
**注意：transcribe 成功后默认删除 .ts 录屏和 wav 以节省磁盘**，设 `LR_KEEP_TS=1` 保留录屏。

### 环境变量
| 变量 | 说明 | 默认 |
|---|---|---|
| LR_MODEL | Whisper 模型（tiny/small/medium/large-v3） | medium |
| LR_THREADS | CPU 线程数 | CPU 核数 |
| LR_KEEP_TS | 设为 1 保留回放文件 | 不保留 |
| LR_CONFIG | 配置 JSON（ASR 纠错词、提示词、车型目标年龄、线索成本区间），见 `scripts/config.example.json` | 内置默认 |
| LR_PROMPT | 覆盖 ASR 提示词 | 配置中的 asr_prompt |
| LR_BASE / LR_INBOX / LR_OUT | run_day 的工作目录 / 输入 / 输出 | 当前目录 / inbox / out |
| LR_PYTHON | run_day 使用的 Python | python3 |

### 输出
- `_transcript.txt`：每行 `HH:MM:SS 话术`（视频 0 秒 = 开播时间）
- `_frames/`：6 张均匀截帧，用于检查画面
- `_gaps.txt` / `_meta.json`：超过 30 秒的无声空档
- `_align.csv` / `_align.md`：每分钟数据 + 该分钟前 1–2 分钟话术（大屏通常滞后 1–2 分钟），标记 线索 / 卡片点击高峰 / 小风车高峰 / 进入高峰 / 在线为0
- `_verdicts.json`：线索成本、曝光进入率、人均停留、目标年龄、漏斗判定
- `summary.md`：全天汇总骨架（数据已填，得分与文字分析待写）

## metrics.json 格式
| 字段 | 说明 |
|---|---|
| start_beijing / end_beijing | 开播/下播时间 HH:MM:SS（与回放起点一致） |
| anchor, car | 主播、车型（车型关键词用于匹配目标年龄） |
| headline | spend 消耗, leads 线索, exposure 曝光, entries 进入, entry_rate 进入率%, avg_watch_s 人均停留秒, card_clicks 卡片点击, windmill_clicks 小风车点击, age_dist 年龄分布文字 |
| lead_times | 留资时间列表 HH:MM:SS |
| per_minute | 每分钟 `{time "HH:MM", entries, online, leads, card_clicks, windmill_clicks}`，可只填关键分钟 |

完整示例见 `example_metrics.json`（虚构数据）。

## 判定标准（付费投流直播间）
- 核心看左下角流量漏斗：曝光 → 进入 → 小风车/讲解卡点击 → 全场景线索
- 单条线索成本 38–60 元正常；<38 偏低（好）；>60 超标（可按本地行情在配置里调整）
- 曝光进入率 5%–15% 正常
- 人均在线时长 10–15 秒正常，>25 秒异常（多为闲聊、人少拉高）
- 曲线重点看进入人数、商机/线索数、卡片点击数；互动率、小风车点击率仅作参考
- 对照车型目标年龄段（示例：家庭 SUV 30–45 岁，年轻轿车/轿跑 24–35 岁）
- 时区：大屏显示时间可能与直播所在地不同，统一换算后按排班核对

## License
MIT © 2026 Keane Hu
