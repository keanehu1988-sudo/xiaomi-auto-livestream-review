"""共享配置：环境变量 LR_CONFIG 指向 JSON 配置文件（格式见 config.example.json），未设置则用内置默认值。
注意：内置 benchmarks 只是示例参考值，请务必在自己的配置里按城市/预算/投放计划填写。"""
import os, json, sys
DEFAULT = {
    "asr_fixes": {"小米苏七": "小米SU7", "苏七": "SU7", "于七": "YU7", "封车": "小风车", "获取包加": "获取报价", "包加单": "报价单"},
    "asr_prompt": "以下是普通话小米汽车直播的转写，小米SU7，小米YU7，续航，智驾，小风车，获取报价，留资，试驾。",
    "target_ages": {"YU7": "28–40", "SU7 ULTRA": "25–40", "SU7": "24–35"},
    # 示例参考值，不是通用标准；任一项设为 null 即跳过该项判定
    "benchmarks": {"cpl_range": [38, 60], "entry_rate_range": [5, 15],
                   "avg_watch_range": [10, 15], "avg_watch_abnormal_above": 25},
}
def load_config():
    cfg = json.loads(json.dumps(DEFAULT))
    p = os.environ.get("LR_CONFIG")
    if p:
        user = json.load(open(p, encoding="utf-8"))
        if "cpl_range" in user:  # 兼容旧版顶层字段
            user.setdefault("benchmarks", {})["cpl_range"] = user.pop("cpl_range")
        cfg["benchmarks"].update(user.pop("benchmarks", {}) or {})
        cfg.update({k: v for k, v in user.items() if not k.startswith("_")})
    else:
        print("[提示] 未设置 LR_CONFIG，判定使用内置示例参考值，建议按 README 填写你自己的基准。", file=sys.stderr)
    return cfg
