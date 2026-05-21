"""
语音模块 — TTS合成 + 音频播放
从数据库读取音色参数
"""
import os, json, threading, asyncio, tempfile

def _get_cfg():
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from modules.database import get_db_path, ensure_db, get_conn, get_settings
        db_path = ensure_db()
        conn = get_conn(db_path)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users ORDER BY last_login DESC LIMIT 1")
        row = c.fetchone()
        uid = row['user_id'] if row else 0
        conn.close()
        if uid:
            return get_settings(uid)
    except:
        pass
    return {}

_tts_loop = None

def _get_loop():
    global _tts_loop
    if _tts_loop is None:
        _tts_loop = asyncio.new_event_loop()
        threading.Thread(target=_tts_loop.run_forever, daemon=True).start()
    return _tts_loop

def tts(text: str, out_path: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    raw = _get_cfg()
    speed = float(raw.get("tts.speed", 1.0))
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
