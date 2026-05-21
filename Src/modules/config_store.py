"""
配置持久化 - 保存和恢复窗口位置/音量等设置
"""
import os, json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pet_config.json")

DEFAULT = {
    "window_x": -1,
    "window_y": -1,
    "volume": 0.8,
    "tts_enabled": True,
    "check_interval": 30,
}

def load() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT, **json.load(f)}
        except:
            pass
    return dict(DEFAULT)

def save(data: dict):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
