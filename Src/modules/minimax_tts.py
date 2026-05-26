"""
MiniMax TTS API 客户端 — 云端音色克隆
"""
import json, urllib.request, os, tempfile

API_URL = "https://api.minimax.chat/v1/text_to_speech"

def is_available() -> bool:
    return bool(os.environ.get("MINIMAX_API_KEY", ""))

def speak(text: str, ref_audio: str = None) -> bool:
    key = os.environ.get("MINIMAX_API_KEY", "")
    if not key:
        return False

    try:
        payload = {
            "model": "speech-01",
            "text": text,
            "voice_id": "female-shaonv",  # 默认女声
        }
        
        # 音色克隆：上传参考音频
        if ref_audio and os.path.exists(ref_audio):
            with open(ref_audio, 'rb') as f:
                audio_b64 = __import__('base64').b64encode(f.read()).decode()
            payload["voice_id"] = ""  
            payload["audio_file"] = audio_b64
            payload["audio_text"] = "龙之介大人，早上好，我是小女仆"

        data = json.dumps(payload).encode()
        req = urllib.request.Request(API_URL, data=data,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST")
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio_data = resp.read()
        
        tmp = os.path.join(tempfile.gettempdir(), "minimax_tts.mp3")
        with open(tmp, "wb") as f:
            f.write(audio_data)
        
        import soundfile as sf, sounddevice as sd
        data, sr = sf.read(tmp)
        sd.play(data, sr)
        sd.wait()
        return True
        
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"MiniMax API错误 [{e.code}]: {body[:100]}")
    except Exception as e:
        print(f"MiniMax失败: {e}")
    return False
