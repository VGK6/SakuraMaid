"""
语音合成模块 — 多语种TTS引擎
支持: edge-tts (中日英) + sherpa-onnx VITS (中文) + FishSpeech API (未来)
用户可配置语种和音色
"""
import os, json, threading, asyncio, tempfile, re
import numpy as np

# ── 语种配置 ──
LANG_CONFIG = {
    "auto": {
        "label": "自动检测",
        "edge_voice": {
            "zh": "zh-CN-XiaoxiaoNeural",
            "ja": "ja-JP-NanamiNeural",
            "en": "en-US-JennyNeural",
        }
    },
    "zh": {"label": "中文", "edge_voice": "zh-CN-XiaoxiaoNeural"},
    "ja": {"label": "日文", "edge_voice": "ja-JP-NanamiNeural"},
    "en": {"label": "英文", "edge_voice": "en-US-JennyNeural"},
}

_tts_loop = None
_sherpa_tts = None

# ── 模型路径 ──
VITS_MODEL_DIR = r"D:\自律资料合集\GitHub开源项目\枫云AI虚拟伙伴Web版v4.0\data\model\TTS\sherpa-onnx-vits-zh-ll"
VITS_MODEL = os.path.join(VITS_MODEL_DIR, "model.onnx")
VITS_TOKENS = os.path.join(VITS_MODEL_DIR, "tokens.txt")


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
        except Exception as e:
            print(f"本地TTS初始化失败: {e}")
    return _sherpa_tts


# ── 语言检测 ──

def detect_lang(text: str) -> str:
    """检测文本语种: zh/ja/en"""
    # 检测日文 (平假名/片假名)
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
        return "ja"
    # 检测中文
    if re.search(r'[\u4e00-\u9fff]', text):
        return "zh"
    # 默认英文
    return "en"


# ── TTS合成 ──

def tts_local(text: str, out_path: str, sid: int = 0, speed: float = 1.0) -> bool:
    """本地VITS合成（仅中文）"""
    tts = _get_local_tts()
    if tts is None:
        return False
    try:
        audio = tts.generate(text, sid=sid, speed=speed)
        if audio is not None and len(audio.samples) > 0:
            import soundfile as sf
            sf.write(out_path, audio.samples, audio.sample_rate)
            return True
    except:
        pass
    return False


def tts_edge(text: str, out_path: str, voice: str = "zh-CN-XiaoxiaoNeural",
             speed: float = 1.0) -> bool:
    """edge-tts在线合成（支持中日英）"""
    try:
        import edge_tts
        loop = _get_loop()
        rate = f"{int((speed - 1) * 100):+d}%"
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        future = asyncio.run_coroutine_threadsafe(communicate.save(out_path), loop)
        future.result(timeout=30)
        return True
    except Exception as e:
        print(f"edge-tts失败: {e}")
        return False


# ── 主入口 ──

def speak(text: str, lang: str = "auto", use_local: bool = True, sid: int = 0) -> float:
    """
    语音播报（多语种）
    lang: auto=自动检测, zh=中文, ja=日文, en=英文
    优先级: FishSpeech API → edge-tts → sherpa-onnx VITS
    """
    # 读取用户设置的TTS模式
    # 读取TTS设置
    _tts_mode = "api"
    _tts_provider = ""
    try:
        import os, sqlite3
        _db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "SakuraMaid_DB.s3db")
        _conn = sqlite3.connect(_db, timeout=5)
        _c = _conn.cursor()
        _c.execute("SELECT value FROM settings WHERE category='tts' AND key='mode' ORDER BY rowid DESC LIMIT 1")
        _r = _c.fetchone()
        if _r: _tts_mode = _r[0]
        _c.execute("SELECT value FROM settings WHERE category='tts' AND key='api_provider' ORDER BY rowid DESC LIMIT 1")
        _r = _c.fetchone()
        if _r: _tts_provider = _r[0]
        _conn.close()
    except:
        pass
    
    # 1. MiniMax API (仅当mode=api且provider不是Edge时)
    if _tts_mode == "api" and "Edge" not in _tts_provider:
        try:
            from modules.minimax_tts import speak as mini_speak, is_available
            if is_available() and mini_speak(text, lang=lang):
                return len(text) * 0.12
        except:
            pass

    # 2. edge-tts (中日英)
    try:
        # 确定语种和音色
        if lang == "auto":
            detected = detect_lang(text)
            voice = LANG_CONFIG["auto"]["edge_voice"].get(detected, "zh-CN-XiaoxiaoNeural")
        elif lang in LANG_CONFIG:
            voice = LANG_CONFIG[lang]["edge_voice"]
        else:
            voice = "zh-CN-XiaoxiaoNeural"

        tmp = os.path.join(tempfile.gettempdir(), "pet_tts.mp3")
        if tts_edge(text, tmp, voice=voice):
            return _play(tmp)
    except:
        pass

    # 3. sherpa-onnx VITS (仅中文，作为兜底)
    if lang in ("auto", "zh"):
        try:
            tmp = os.path.join(tempfile.gettempdir(), "pet_tts.wav")
            if use_local and _get_local_tts() is not None:
                ok = tts_local(text, tmp, sid=sid)
                if ok:
                    return _play(tmp)
        except:
            pass

    return 0


def _play(path: str) -> float:
    import soundfile as sf, sounddevice as sd
    data, sr = sf.read(path)
    duration = len(data) / sr
    sd.play(data, sr)
    sd.wait()
    return duration


def list_edge_voices() -> dict:
    """返回支持的edge-tts音色"""
    return {
        "zh": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunjianNeural"],
        "ja": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
        "en": ["en-US-JennyNeural", "en-GB-SoniaNeural", "en-US-AriaNeural"],
    }


def get_local_voices() -> list:
    """获取本地VITS可用音色列表"""
    tts = _get_local_tts()
    if tts is None:
        return [{"id": 0, "name": "默认女声"}]
    return [{"id": i, "name": f"音色{i}"} for i in range(tts.num_speakers)]
