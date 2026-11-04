# 小米汽车直播间直播大屏复盘 · xiaomi-auto-livestream-review

> **一句话：把一场小米汽车抖音投流直播的大屏数据和回放话术逐分钟对齐，告诉你哪句话带来了留资、哪句话把人讲跑了。**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg) ![Platform](https://img.shields.io/badge/抖音-巨量直播大屏-black.svg)

面向小米汽车（SU7 / YU7）门店付费投流直播间的复盘 Skill + 脚本工具集：读巨懂车/巨量直播大屏的流量漏斗与趋势曲线，下载回放并转写话术，把话术和关键分钟对齐，按**你自己设定的基准**判定、打分并给出优化建议。其他品牌的汽车直播间改一下配置也能用。

## 适用人群
- 小米汽车门店 / 经销商的直播运营、投手、主播
- 每天要复盘多场付费直播、想把“感觉”变成“数据+原话证据”的团队
- 想让 AI 助手（Claude / Cursor / Grok Bot 等支持 Skill 的工具）自动复盘的人

## 包含什么
- `SKILL.md`：给 AI 助手用的复盘方法（判断思路 + 步骤）
- `scripts/transcribe.py`：回放转写（faster-whisper + opencc），截帧，找 >30 秒空档
- `scripts/align.py`：话术与每分钟数据对齐，自动标记关键分钟，按配置里的基准给出判定
- `scripts/run_day.sh`：批量处理一天所有场次，生成 `summary.md` 骨架
- `scripts/config.example.json`：配置模板（纠错词、车型目标年龄、判定基准）

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
| LR_CONFIG | 配置 JSON（ASR 纠错词、提示词、车型目标年龄、**判定基准 benchmarks**），见 `scripts/config.example.json` | 内置示例值 |
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

## 判定标准：请填你自己的基准
**没有放之四海皆准的标准值。** 线索成本、进入率、停留时长都强烈依赖城市、车型、预算、投放计划和时段。脚本里所有阈值都从配置 `benchmarks` 读取，请复制 `scripts/config.example.json` 为自己的 `config.json` 并修改，运行时设 `LR_CONFIG=config.json`。

| 配置项 | 含义 | 示例参考值（仅供参考） |
|---|---|---|
| `cpl_range` | 单条线索成本正常区间（元），低于下限=偏低（好），高于上限=超标 | `[38, 60]` |
| `entry_rate_range` | 曝光进入率正常区间（%） | `[5, 15]` |
| `avg_watch_range` | 人均在线时长正常区间（秒） | `[10, 15]` |
| `avg_watch_abnormal_above` | 超过即判异常（多为闲聊、人少拉高）（秒） | `25` |
| `target_ages` | 车型关键词 → 目标年龄段 | SU7 `24–35`，YU7 `28–40` |

> ⚠️ 以上**示例参考值**来自作者所在城市某小米汽车门店的付费直播间，**不是通用标准**。未设置 `LR_CONFIG` 时脚本会用它们兜底并在输出里注明“内置示例参考值”。任一项设为 `null` 即跳过该项判定。

### 怎么定出自己的基准（5 分钟）
1. 拿最近 **2–4 周**、同一账号、同类投放计划的场次（至少 10 场），记下每场的消耗、线索、曝光、进入、人均停留。
2. 每个指标算**中位数**（比平均数更不怕极端场次）。
3. 正常区间可取 **P25–P75**（四分位）；或者“中位数 ±25%”。线索成本上限也可以直接用你的**考核目标成本**。
4. 停留时长的“异常上限”可取 P90，或你观察到“人少闲聊”场次的典型值。
5. 每月或换投放策略后重算一次；大促、新车上市期间单独一套配置。

其他复盘要点：
- 核心看左下角流量漏斗：曝光 → 进入 → 小风车/讲解卡点击 → 全场景线索
- 曲线重点看进入人数、商机/线索数、卡片点击数；互动率、小风车点击率仅作参考
- 时区：大屏显示时间可能与直播所在地不同，统一换算后按排班核对

## 效果示例
用仓库自带的**虚构**数据 `example_metrics.json`（小米SU7 示例场次）运行：
```text
$ LR_CONFIG=scripts/config.example.json scripts/align.py demo_transcript.txt example_metrics.json demo
线索成本: 60.00 元 → 正常(38–60元)
曝光进入率: 7.50% → 正常(5–15%)
人均停留: 14s → 正常(10–15s)
_基准来源: LR_CONFIG 配置
目标年龄: 小米SU7（示例） 目标 24–35 岁；实际年龄分布：24–30岁 38%，31–40岁 33%
漏斗: 曝光2000 → 进入150 → 卡片30/风车6 → 线索2
```
`demo_align.md` 片段（大屏通常滞后 1–2 分钟，所以对的是前 1–2 分钟的话术）：

| 时间 | 进入 | 在线 | 线索 | 卡片 | 风车 | 标记 | 前1–2分钟话术 |
|---|---|---|---|---|---|---|---|
| 19:45 | 6 | 7 | 1 | 2 | 0 | 线索,卡片点击高峰,进入高峰 | 家人们点一下小风车获取小米SU7报价 / 左下角小风车留个电话安排试驾 |
| 20:18 | 5 | 7 | 1 | 0 | 1 | 线索,进入高峰 | 聊聊天气 / 点讲解卡看SU7续航 |

同一份数据如果你的基准是 `cpl_range: [80, 150]`，线索成本会判为“偏低，好(<80元)”——判定完全跟着你的配置走。

## FAQ
**Q：不是小米汽车的直播间能用吗？** 能。改 `target_ages`、`asr_fixes`、`asr_prompt` 为你的车型即可，脚本逻辑与品牌无关。
**Q：一定要有回放视频吗？** 不一定。没有回放可以手写 `HH:MM:SS 话术` 格式的转写文件直接跑 `align.py`。
**Q：需要 GPU 吗？** 不需要，CPU 可跑；慢的话设 `LR_MODEL=small`。
**Q：会抓取或登录我的抖音/巨量账号吗？** 不会。仓库不含任何登录、抓取代码，大屏数据需你自己（或 AI 助手在浏览器中）读取后填入 metrics.json。
**Q：示例里的 38–60 元能直接用吗？** 不建议。那只是一家门店的参考值，请按上面的方法用自己的历史数据定。

## English
**xiaomi-auto-livestream-review** is a Skill + script toolkit for reviewing paid Douyin livestreams of Xiaomi Auto (SU7 / YU7) dealers. It transcribes the replay (faster-whisper), aligns each minute of the Juliang live dashboard (entries, online, leads, card / "windmill" clicks) with what the host said 1–2 minutes earlier, flags key minutes, and judges cost-per-lead, entry rate and watch time against **your own benchmarks** in `config.json` (the bundled numbers are example values only). Works for other car brands by editing the config. No login or scraping code included.

## License
MIT © 2026 Keane Hu
