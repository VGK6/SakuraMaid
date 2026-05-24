"""
语音合成模块 — 本地VITS TTS (sherpa-onnx) + 备用edge-tts
支持本地女声和在线语速调节
"""
import os, json, threading, asyncio, tempfile
import numpy as np

# ── 本地VITS模型路径 ──
VITS_MODEL_DIR = r"D:\自律资料合集\GitHub开源项目\枫云AI虚拟伙伴Web版v4.0\data\model\TTS\sherpa-onnx-vits-zh-ll"
VITS_MODEL = os.path.join(VITS_MODEL_DIR, "model.onnx")
VITS_TOKENS = os.path.join(VITS_MODEL_DIR, "tokens.txt")

_tts_loop = None
_sherpa_tts = None

def _get_loop():
    global _tts_loop
    if _tts_loop is None:
        _tts_loop = asyncio.new_event_loop()
        threading.Thread(target=_tts_loop.run_forever, daemon=True).start()
    return _tts_loop

def _get_local_tts():
    """初始化本地VITS TTS引擎"""
    global _sherpa_tts
    if _sherpa_tts is None and os.path.exists(VITS_MODEL):
        try:
            import sherpa_onnx
            config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=VITS_MODEL,
                        tokens=VITS_TOKENS,
                        lexicon=os.path.join(VITS_MODEL_DIR, "lexicon.txt"),
                    ),
                ),
            )
            _sherpa_tts = sherpa_onnx.OfflineTts(config)
            print(f"✅ 本地TTS引擎就绪 (zh-LL 116MB)")
        except Exception as e:
            print(f"❌ 本地TTS初始化失败: {e}")
    return _sherpa_tts

def tts_local(text: str, out_path: str, sid: int = 0, speed: float = 1.0) -> bool:
    """使用本地VITS模型合成语音"""
    tts = _get_local_tts()
    if tts is None:
        return False
    try:
        audio = tts.generate(text, sid=sid, speed=speed)
        if audio is not None and len(audio.samples) > 0:
            import soundfile as sf
            sf.write(out_path, audio.samples, audio.sample_rate)
            return True
    except Exception as e:
        print(f"TTS本地合成失败: {e}")
    return False

def tts_edge(text: str, out_path: str, voice: str = "zh-CN-XiaoxiaoNeural", speed: float = 1.0) -> bool:
    """使用edge-tts在线合成（备用）"""
    try:
        import edge_tts
        loop = _get_loop()
        rate = f"{int((speed - 1) * 100):+d}%"
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        future = asyncio.run_coroutine_threadsafe(communicate.save(out_path), loop)
        future.result(timeout=30)
        return True
    except Exception as e:
        print(f"TTS在线合成失败: {e}")
        return False

def speak(text: str, use_local: bool = True, sid: int = 0) -> float:
    """语音播报，返回音频时长(秒)，失败返回0"""
    try:
        tmp = os.path.join(tempfile.gettempdir(), "pet_tts.wav")
        
        # 尝试本地
        if use_local and _get_local_tts() is not None:
            ok = tts_local(text, tmp, sid=sid)
            if ok:
                return _play(tmp)
        
        # 回退在线
        ok = tts_edge(text, tmp)
        if ok:
            return _play(tmp)
    except Exception as e:
        print(f"语音播报失败: {e}")
    return 0

def _play(path: str) -> float:
    import soundfile as sf, sounddevice as sd
    data, sr = sf.read(path)
    duration = len(data) / sr
    sd.play(data, sr)
    sd.wait()
    return duration

def get_local_voices() -> list:
    """获取本地VITS可用音色列表"""
    tts = _get_local_tts()
    if tts is None:
        return [{"id": 0, "name": "默认女声"}]
    # sherpa-onnx vits通常只有1个音色
    return [{"id": i, "name": f"音色{i}"} for i in range(tts.num_speakers)]
