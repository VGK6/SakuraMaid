"""
语音识别模块 — sherpa-onnx sense-voice (枫云AI同款方案)
PyAudio录音 → sense-voice识别 → 文字
"""
import os, json, wave, struct, threading, time, numpy as np
import pyaudio

# sense-voice模型路径 (复用枫云AI的模型)
MODEL_DIR = r"D:\自律资料合集\GitHub开源项目\枫云AI虚拟伙伴Web版v4.0\data\model\ASR\sherpa-onnx-sense-voice-zh-en-ja-ko-yue"
MODEL_PATH = os.path.join(MODEL_DIR, "model.int8.onnx")
TOKENS_PATH = os.path.join(MODEL_DIR, "tokens.txt")

_recognizer = None
_pyaudio_instance = None
_is_listening = False

# 录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_SECONDS = 1.5  # 静音1.5秒后停止
SILENCE_CHUNKS = int(SILENCE_SECONDS * RATE / CHUNK)


def _rms(data):
    """计算音频均方根"""
    return np.sqrt(np.mean(np.frombuffer(data, dtype=np.int16) ** 2))


def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        if not os.path.exists(MODEL_PATH):
            print(f"❌ sense-voice模型未找到: {MODEL_PATH}")
            return None
        import sherpa_onnx
        _recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=MODEL_PATH, tokens=TOKENS_PATH, use_itn=True,
            num_threads=int(os.cpu_count()) - 1 or 1)
        print(f"✅ sense-voice模型加载 ({os.path.getsize(MODEL_PATH)/1024/1024:.0f}MB)")
    return _recognizer


def _get_pyaudio():
    global _pyaudio_instance
    if _pyaudio_instance is None:
        _pyaudio_instance = pyaudio.PyAudio()
    return _pyaudio_instance


def list_devices() -> list:
    """列出可用的麦克风设备"""
    p = _get_pyaudio()
    mics = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            mics.append({"id": i, "name": info['name'], "channels": info['maxInputChannels'],
                        "default": i == p.get_default_input_device_info()['index']})
    return mics


def get_default_device() -> dict:
    """获取默认输入设备"""
    p = _get_pyaudio()
    try:
        idx = p.get_default_input_device_info()['index']
        info = p.get_device_info_by_index(idx)
        return {"id": idx, "name": info['name'], "channels": info['maxInputChannels']}
    except:
        return {"id": 0, "name": "未知"}


def test_mic(device: int = None, duration: float = 3.0) -> dict:
    """测试麦克风音量水平"""
    p = _get_pyaudio()
    dev = device if device is not None else p.get_default_input_device_info()['index']
    print(f"🎤 测试麦克风 [{dev}]...")

    levels = []
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=dev)
    start = time.time()
    while time.time() - start < duration:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            levels.append(_rms(data))
        except:
            pass
    stream.stop_stream()
    stream.close()

    max_l = int(max(levels)) if levels else 0
    avg_l = int(np.mean(levels)) if levels else 0
    noise = int(np.percentile(levels, 10)) if levels else 0

    if max_l < 50:
        verdict = "❌ 几乎没声音，请检查麦克风权限和音量"
    elif max_l < 500:
        verdict = "⚠️ 声音太小，请靠近麦克风或调高音量"
    elif avg_l > 5000:
        verdict = f"✅ 音量正常"
    else:
        verdict = f"✅ 收音正常 (峰值={max_l})"

    print(f"  峰值: {max_l}, 平均: {avg_l}, 底噪: {noise}")
    print(f"  {verdict}")
    return {"max_amp": max_l, "avg_amp": avg_l, "noise_floor": noise, "verdict": verdict}


def listen(timeout: float = 10.0, silence_limit: float = 1.5, device: int = None) -> str:
    """
    录音并识别语音（PyAudio + sense-voice）
    
    参数:
        timeout: 最大录音时长
        silence_limit: 静音秒数后停止
        device: 麦克风设备ID, None用默认
    """
    global _is_listening
    rec = _get_recognizer()
    if rec is None:
        return ""

    p = _get_pyaudio()
    dev = device if device is not None else p.get_default_input_device_info()['index']
    silence_chunks = int(silence_limit * RATE / CHUNK)

    _is_listening = True
    frames = []
    silence_counter = 0
    has_audio = False

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=dev)

    try:
        stream.start_stream()
        start_time = time.time()
        last_print = 0

        while time.time() - start_time < timeout:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

                current_rms = _rms(data)
                has_audio = has_audio or (current_rms > 15)  # 极低阈值

                if current_rms > 30:
                    silence_counter = 0
                else:
                    silence_counter += 1

                # 显示音量
                now = time.time()
                if now - last_print > 1:
                    bar = "█" * min(int(current_rms / 100), 40)
                    label = f"{'🔊' if current_rms > 100 else '🔇'}"
                    print(f"  {label} {int(current_rms):5d} {bar}")
                    last_print = now

                # 已有声音后静音超时 → 停止（但至少录3秒）
                if has_audio and silence_counter > silence_chunks and time.time() - start_time > 3:
                    break

            except Exception as e:
                print(f"  录音异常: {e}")
                break

        stream.stop_stream()
        _is_listening = False

        # 保存到临时wav文件
        cache_path = os.path.join(os.environ.get('TEMP', '/tmp'), "pet_record.wav")
        with wave.open(cache_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        # 检查录音时长
        duration = len(frames) * CHUNK / RATE
        if duration < 1.0 or not has_audio:
            return ""

        # sense-voice识别
        import soundfile as sf
        audio_data, sr = sf.read(cache_path, dtype="float32", always_2d=True)

        asr_stream = rec.create_stream()
        asr_stream.accept_waveform(sr, audio_data[:, 0])
        rec.decode_stream(asr_stream)
        result = json.loads(str(asr_stream.result))
        text = result.get('text', '').strip()

        # 过滤无效结果
        if text in ("", "The.", "the."):
            return ""

        return text

    except Exception as e:
        print(f"❌ 语音识别失败: {e}")
        return ""
    finally:
        _is_listening = False
        try:
            stream.close()
        except:
            pass


def listen_async(callback, timeout: float = 10.0, device: int = None):
    def _worker():
        text = listen(timeout=timeout, device=device)
        if text:
            callback(text)
    threading.Thread(target=_worker, daemon=True).start()


def is_listening() -> bool:
    return _is_listening
