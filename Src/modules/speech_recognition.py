"""
语音识别模块 — Vosk本地离线语音识别
支持设备选择和静音检测自动停止
"""
import os, json, threading, queue, time
import sounddevice as sd
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "resourses", "models", "vosk", "vosk-model-small-cn-0.22")

_recognizer = None
_audio_q = queue.Queue()
_is_listening = False

def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        from vosk import Model, KaldiRecognizer
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Vosk模型未找到: {MODEL_PATH}")
            return None
        model = Model(MODEL_PATH)
        _recognizer = KaldiRecognizer(model, 16000)
    return _recognizer

def list_devices() -> list:
    """列出可用的麦克风设备"""
    devices = sd.query_devices()
    mics = []
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            mics.append({"id": i, "name": d['name'], "channels": d['max_input_channels']})
    return mics

def get_default_device() -> dict:
    """获取默认输入设备"""
    try:
        idx = sd.default.device[0]
        if idx is None:
            info = sd.query_devices()
            for i, d in enumerate(info):
                if d['max_input_channels'] > 0:
                    return {"id": i, "name": d['name']}
        info = sd.query_devices(idx)
        return {"id": idx, "name": info['name']}
    except:
        return {"id": 0, "name": "未知"}

def listen(timeout: float = 10.0, silence_limit: float = 2.0, device: int = None) -> str:
    """
    录音并识别语音，返回文本
    
    参数:
        timeout: 最大录音时长(秒)
        silence_limit: 静音多少秒后自动停止
        device: 麦克风设备ID, None用默认
    """
    global _is_listening
    rec = _get_recognizer()
    if rec is None:
        return ""

    _is_listening = True
    _audio_q = queue.Queue()

    stream = sd.RawInputStream(
        samplerate=16000, blocksize=8000, dtype='int16',
        channels=1, callback=_audio_callback, device=device
    )

    try:
        stream.start()
        start_time = time.time()
        last_sound_time = time.time()
        result_text = ""
        has_any_result = False

        while time.time() - start_time < timeout:
            try:
                data = _audio_q.get(timeout=0.3)
                # 检测是否有声音（简单幅值检测）
                import struct
                samples = struct.unpack(f"{len(data)//2}h", data)
                amp = max(abs(s) for s in samples) if samples else 0

                if amp > 500:  # 有声音
                    last_sound_time = time.time()

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        result_text += " " + text
                        has_any_result = True
                        last_sound_time = time.time()

                # 静音超时且已经有结果 → 停止
                if has_any_result and (time.time() - last_sound_time > silence_limit):
                    break

            except queue.Empty:
                pass

        # 获取最终结果
        final = json.loads(rec.FinalResult())
        final_text = final.get("text", "")

        stream.stop()
        _is_listening = False

        full = (result_text + " " + final_text).strip()
        return full

    except Exception as e:
        print(f"录音失败: {e}")
        return ""
    finally:
        _is_listening = False
        try:
            stream.close()
        except:
            pass

def _audio_callback(indata, frames, time_info, status):
    """录音回调"""
    if status:
        print(f"录音状态: {status}")
    _audio_q.put(bytes(indata))

def listen_async(callback, timeout: float = 10.0, device: int = None):
    """异步录音识别"""
    def _worker():
        text = listen(timeout=timeout, device=device)
        if text:
            callback(text)
    threading.Thread(target=_worker, daemon=True).start()

def is_listening() -> bool:
    return _is_listening
