"""
LLM客户端 - 调用DeepSeek API
"""
import os, json, urllib.request

def _get_api_key() -> str:
    """从环境变量或AstrBot配置获取API Key"""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key
    try:
        cfg_path = os.path.expanduser("~") + "/.astrbot/data/cmd_config.json"
        with open(cfg_path, 'r', encoding='utf-8-sig') as f:
            cfg = json.load(f)
        for s in cfg.get('provider_sources', []):
            if s.get('id') == 'deepseek':
                keys = s.get('key', [])
                if keys:
                    return keys[0]
    except:
        pass
    return ""

API_KEY = _get_api_key()
API_URL = "https://api.deepseek.com/v1/chat/completions"
SYSTEM_PROMPT = "你是樱花庄的小女仆AI，简短可爱地回答，不超过20字。"

def chat(text: str, system: str = None) -> str:
    """发送对话请求"""
    if not API_KEY:
        return "小女仆还没连上服务器呢~"
    data = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system or SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "max_tokens": 200
    }).encode()
    req = urllib.request.Request(API_URL, data=data,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]
