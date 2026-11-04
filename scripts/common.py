"""共享配置：环境变量 LR_CONFIG 指向 JSON 配置文件（格式见 config.example.json），未设置则用内置默认值。"""
import os, json
DEFAULT = {
    "asr_fixes": {"鹏城": "澎程", "鹏程": "澎程", "封车": "小风车", "获取包加": "获取报价", "包加单": "报价单"},
    "asr_prompt": "以下是普通话汽车直播带货的转写，增程，七座，空悬，小风车，获取报价，留资。",
    "target_ages": {"N70": "30–45", "N90": "30–45", "澎程": "30–45", "YU7": "24–35", "SU7": "24–35"},
    "cpl_range": [38, 60],
}
def load_config():
    cfg = dict(DEFAULT)
    p = os.environ.get("LR_CONFIG")
    if p: cfg.update(json.load(open(p, encoding="utf-8")))
    return cfg
