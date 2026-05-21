"""
语音模块 - TTS合成 + 音频播放
"""
import os, threading, asyncio, tempfile

_tts_loop = None
_tts_lock = threading.Lock()

def _get_loop():
    global _tts_loop
    if _tts_loop is None:
        _tts_loop = asyncio.new_event_loop()
        threading.Thread(target=_tts_loop.run_forever, daemon=True).start()
    return _tts_loop

def tts(text: str, out_path: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """文字转语音"""
    import edge_tts
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(
        edge_tts.Communicate(text, voice).save(out_path), loop)
    future.result(timeout=30)

def play_audio(path: str):
    """播放音频文件"""
    import soundfile as sf
    import sounddevice as sd
    data, sr = sf.read(path)
    sd.play(data, sr)
    sd.wait()

def speak(text: str) -> bool:
    """合成并播放语音"""
    try:
        tmp = os.path.join(tempfile.gettempdir(), "pet_tts.mp3")
        tts(text, tmp)
        play_audio(tmp)
        return True
    except Exception as e:
        print(f"TTS失败: {e}")
        return False
