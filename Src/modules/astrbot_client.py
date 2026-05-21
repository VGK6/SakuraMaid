"""
AstrBot API 客户端 — 从数据库读取配置
"""
import os, json, urllib.request

def _get_cfg():
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from modules.database import get_db_path, ensure_db, get_conn, get_settings
        db_path = ensure_db()
        conn = get_conn(db_path)
        c = conn.cursor()
        c.execute("SELECT last_insert_rowid()")  # dummy
        # 获取最后登录用户的user_id
        try:
            c.execute("SELECT user_id FROM users ORDER BY last_login DESC LIMIT 1")
            row = c.fetchone()
            uid = row['user_id'] if row else 0
        except:
            uid = 0
        conn.close()
        if uid:
            return get_settings(uid)
    except:
        pass
    return {}

API_KEY = ""
BASE_URL = "http://127.0.0.1:6185"
TIMEOUT = 30

def _reload():
    global API_KEY, BASE_URL, TIMEOUT
    raw = _get_cfg()
    API_KEY = raw.get("astrbot.api_key", os.environ.get("ASTRBOT_API_KEY", ""))
    BASE_URL = raw.get("astrbot.url", "http://127.0.0.1:6185")
    try:
        TIMEOUT = 30
    except:
        pass

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
