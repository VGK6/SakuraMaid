"""
FishSpeech TTS 客户端 — 通过HTTP调用独立环境的TTS服务
"""
import json, urllib.request, base64, os, tempfile, threading

FISH_HOST = "http://127.0.0.1:18765"

_fish_available = None

def is_available() -> bool:
    """检查FishSpeech服务是否在线"""
    global _fish_available
    try:
        req = urllib.request.Request(f"{FISH_HOST}/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            _fish_available = data.get("status") == "ok"
            return _fish_available
    except:
        _fish_available = False
        return False

def speak(text: str, ref_audio: str = None) -> bool:
    """
    使用FishSpeech合成语音并播放
    ref_audio: 参考音频路径（用于音色克隆）
    """
    if not is_available():
        return False

    try:
        # 准备请求
        data = {"text": text}
        if ref_audio and os.path.exists(ref_audio):
            with open(ref_audio, "rb") as f:
                data["ref_audio"] = base64.b64encode(f.read()).decode()

        req = urllib.request.Request(f"{FISH_HOST}/tts",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST")

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            if "audio" in result:
                audio_data = base64.b64decode(result["audio"])
                tmp = os.path.join(tempfile.gettempdir(), "fish_tts.wav")
                with open(tmp, "wb") as f:
                    f.write(audio_data)
                # 播放
                import soundfile as sf, sounddevice as sd
                data, sr = sf.read(tmp)
                sd.play(data, sr)
                sd.wait()
                return True
    except Exception as e:
        print(f"FishSpeech调用失败: {e}")
    return False

def start_server():
    """启动FishSpeech服务进程（如果未运行）"""
    if is_available():
        return True
    try:
        import subprocess
        server_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "FishEnv", "tts_server.py")
        if os.path.exists(server_script):
            fish_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       "FishEnv", "Scripts", "python.exe")
            subprocess.Popen([fish_python, server_script],
                           creationflags=subprocess.CREATE_NO_WINDOW)
            threading.Thread(target=_wait_ready, daemon=True).start()
            return True
    except:
        pass
    return False

def _wait_ready():
    import time
    for i in range(30):
        time.sleep(2)
        if is_available():
            print("✅ FishSpeech服务已就绪")
            return
    print("⚠️ FishSpeech服务启动超时")
