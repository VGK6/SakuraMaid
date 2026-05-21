"""
AstrBot API 客户端 - 通过API Key调用本地AstrBot服务
"""
import os, json, urllib.request, re

API_KEY = os.environ.get("ASTRBOT_API_KEY", "abk_pHR4OJsje0xanu0dXxSEGqATFZY_eUNmfPbNyed5EkQ")
BASE_URL = "http://127.0.0.1:6185"

def chat(message: str, session_id: str = "maid_pet", username: str = "龙之介大人") -> str:
    """通过AstrBot API对话，返回AI回复文本"""
    data = json.dumps({
        "message": message,
        "session_id": session_id,
        "username": username
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/v1/chat",
        data=data,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            # 解析SSE流，提取所有plain类型的data
            replies = []
            for line in body.split('\n'):
                if line.startswith('data: '):
                    try:
                        chunk = json.loads(line[6:])
                        if chunk.get('type') == 'plain':
                            replies.append(chunk['data'])
                    except:
                        pass
            # 合并回复
            full = ''.join(replies)
            if full:
                # 尝试解析嵌套JSON
                try:
                    parsed = json.loads(full)
                    if isinstance(parsed, dict):
                        return json.dumps(parsed, ensure_ascii=False)
                except:
                    pass
            return full
        return "（小女仆没收到回复...）"
    except Exception as e:
        return f"💭 AstrBot连接失败: {str(e)[:40]}"

def check_status() -> dict:
    """检查API连通性——用api/v1/chat轻量调用测试"""
    try:
        data = json.dumps({"message": "ping", "session_id": "_health_check"}).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/v1/chat",
            data=data,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {API_KEY}"},
            method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"online": True, "status": resp.status}
    except Exception as e:
        return {"online": False, "status": str(e)[:30]}
