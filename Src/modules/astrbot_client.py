"""
AstrBot API 客户端 — 从pet_config.json读取配置
"""
import os, json, urllib.request

def _get_cfg():
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "pet_config.json")
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

API_KEY = ""
BASE_URL = "http://127.0.0.1:6185"
TIMEOUT = 30

def _reload():
    global API_KEY, BASE_URL, TIMEOUT
    cfg = _get_cfg()
    API_KEY = cfg.get("astrbot_api_key", os.environ.get("ASTRBOT_API_KEY", ""))
    BASE_URL = cfg.get("astrbot_url", "http://127.0.0.1:6185")
    TIMEOUT = cfg.get("api_timeout", 30)

_reload()

def chat(message: str, session_id: str = "maid_pet", username: str = "龙之介大人") -> str:
    _reload()
    if not API_KEY:
        return "⚠️ 未配置API Key，请在设置中填写"
    data = json.dumps({
        "message": message, "session_id": session_id, "username": username
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/v1/chat", data=data,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode()
            replies = []
            for line in body.split('\n'):
                if line.startswith('data: '):
                    try:
                        chunk = json.loads(line[6:])
                        if chunk.get('type') == 'plain':
                            replies.append(chunk['data'])
                    except:
                        pass
            return ''.join(replies)
    except Exception as e:
        return f"💭 连接失败: {str(e)[:30]}"

def check_status() -> dict:
    _reload()
    try:
        data = json.dumps({"message": "ping", "session_id": "_check"}).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/v1/chat", data=data,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {API_KEY}"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"online": True, "status": resp.status}
    except:
        return {"online": False, "status": "离线"}
