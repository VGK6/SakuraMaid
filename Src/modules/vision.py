"""
视觉理解模块 — 通过Ollama调用llava看图
支持: 图片描述、屏幕截图分析、摄像头画面理解
"""
import json, urllib.request, base64, os, threading

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "llava:latest"

def _ask_llava(prompt: str, image_b64: str) -> str:
    """调用Ollama llava分析图片"""
    data = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt, "images": [image_b64]}],
        "stream": False
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=data,
                                headers={"Content-Type": "application/json"},
                                method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")
    except Exception as e:
        return f"llava调用失败: {str(e)[:40]}"

def describe_image(image_path: str) -> str:
    """描述一张图片的内容"""
    if not os.path.exists(image_path):
        return "图片文件不存在"
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return _ask_llava("请描述这张图片里有什么", b64)

def describe_screen() -> str:
    """截屏并用llava分析屏幕内容"""
    try:
        from modules.screen_capture import ScreenCapture
        sc = ScreenCapture()
        path = sc.save_screenshot()
        result = describe_image(path)
        return result
    except Exception as e:
        return f"屏幕分析失败: {e}"

def analyze_with_question(image_path: str, question: str) -> str:
    """针对图片提出具体问题"""
    if not os.path.exists(image_path):
        return "图片文件不存在"
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return _ask_llava(question, b64)

def is_available() -> bool:
    """检查llava模型是否可用"""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return any(MODEL in m['name'] for m in data.get('models', []))
    except:
        return False
