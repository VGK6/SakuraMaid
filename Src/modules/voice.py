"""
语音模块 — TTS合成 + 音频播放
从pet_config.json读取音色参数
"""
import os, json, threading, asyncio, tempfile

def _get_cfg():
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "pet_config.json")
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

_tts_loop = None

def _get_loop():
    global _tts_loop
    if _tts_loop is None:
        _tts_loop = asyncio.new_event_loop()
        threading.Thread(target=_tts_loop.run_forever, daemon=True).start()
    return _tts_loop

def tts(text: str, out_path: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    cfg = _get_cfg()
    speed = cfg.get("tts_speed", 1.0)
    pitch = cfg.get("tts_pitch", 0.0)
    volume = cfg.get("tts_volume", 80)
    import edge_tts
    loop = _get_loop()
    communicate = edge_tts.Communicate(text, voice, rate=f"{int((speed-1)*100):+d}%")
    future = asyncio.run_coroutine_threadsafe(communicate.save(out_path), loop)
    future.result(timeout=30)

def play_audio(path: str):
    import soundfile as sf, sounddevice as sd
    data, sr = sf.read(path)
    sd.play(data, sr)
    sd.wait()

def speak(text: str) -> bool:
    try:
        tmp = os.path.join(tempfile.gettempdir(), "pet_tts.mp3")
        tts(text, tmp)
        play_audio(tmp)
        return True
    except Exception as e:
        print(f"TTS失败: {e}")
        return False
