"""
FishSpeech TTS API 客户端 — 在线API方式（无需本地模型）
"""
import json, urllib.request, base64, os, tempfile

# FishSpeech官方API
API_URL = "https://api.fish.audio/v1/tts"

def is_available() -> bool:
    """检查API Key是否已配置"""
    key = os.environ.get("FISH_API_KEY", "")
    return bool(key)

def speak(text: str, ref_audio: str = None) -> bool:
    """
    使用FishSpeech在线API合成语音并播放
    ref_audio: 参考音频路径（用于音色克隆）
    """
    key = os.environ.get("FISH_API_KEY", "")
    if not key:
        return False

    try:
        # 构建请求
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "text": text,
            "format": "wav",
            "voice": "845a1ad1b00a4f91a14662af6f47de46",  # 小女仆音色(需创建)
        }
        
        # 如果有参考音频，上传用于音色克隆
        if ref_audio and os.path.exists(ref_audio):
            # 先上传参考音频获取voice_id
            pass  # 需要实现音频上传逻辑
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            audio_data = resp.read()
            
        tmp = os.path.join(tempfile.gettempdir(), "fish_api_tts.wav")
        with open(tmp, "wb") as f:
            f.write(audio_data)
        
        import soundfile as sf, sounddevice as sd
        data, sr = sf.read(tmp)
        sd.play(data, sr)
        sd.wait()
        return True
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"FishSpeech API错误 [{e.code}]: {error_body[:100]}")
    except Exception as e:
        print(f"FishSpeech API失败: {e}")
    return False
