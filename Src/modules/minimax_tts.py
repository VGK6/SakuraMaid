"""
MiniMax TTS API 客户端
启动时自动克隆音色，后续直接使用
"""
import json, urllib.request, os, tempfile, uuid, threading

API_URL = "https://api.minimax.chat/v1/text_to_speech"
CLONE_URL = "https://api.minimax.chat/v1/voice_clone"
UPLOAD_URL = "https://api.minimax.chat/v1/files/upload"

_voice_id = "female-shaonv"  # 默认音色

def is_available() -> bool:
    return bool(os.environ.get("MINIMAX_API_KEY", ""))

def _upload_file(file_path: str) -> str:
    """上传音频文件到MiniMax，返回file_id"""
    import uuid as _uuid
    boundary = "----" + str(_uuid.uuid4()).replace('-', '')
    with open(file_path, 'rb') as f:
        audio_data = f.read()
    body_parts = []
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="purpose"')
    body_parts.append(b"")
    body_parts.append(b"voice_clone")
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"'.encode())
    body_parts.append(b"Content-Type: audio/wav")
    body_parts.append(b"")
    body_parts.append(audio_data)
    body_parts.append(f"--{boundary}--".encode())
    body_data = b"\r\n".join(body_parts)
    
    key = os.environ.get("MINIMAX_API_KEY", "")
    req = urllib.request.Request(UPLOAD_URL, data=body_data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
        return str(result.get('file', {}).get('file_id', ''))

def _clone_voice(file_id: str, voice_name: str = "小女仆") -> str:
    """用file_id克隆音色，返回voice_id"""
    global _voice_id
    key = os.environ.get("MINIMAX_API_KEY", "")
    new_vid = "pet_" + str(uuid.uuid4()).replace('-', '')[:8]
    
    boundary = "----" + str(uuid.uuid4()).replace('-', '')
    body_parts = []
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="voice_id"')
    body_parts.append(b"")
    body_parts.append(new_vid.encode())
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="voice_name"')
    body_parts.append(b"")
    body_parts.append(voice_name.encode('utf-8'))
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="file_id"')
    body_parts.append(b"")
    body_parts.append(file_id.encode())
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="audio_text"')
    body_parts.append(b"")
    body_parts.append("龙之介大人，早上好，我是小女仆".encode('utf-8'))
    body_parts.append(f"--{boundary}--".encode())
    body_data = b"\r\n".join(body_parts)
    
    req = urllib.request.Request(CLONE_URL, data=body_data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        if result.get('base_resp', {}).get('status_code') == 0:
            _voice_id = new_vid
            return new_vid
    return ""

def init(ref_audio: str = None):
    """启动时初始化：检测参考音频是否变更，必要时重新克隆"""
    global _voice_id
    key = os.environ.get("MINIMAX_API_KEY", "")
    if not key:
        return
    
    custom_id = os.environ.get("MINIMAX_VOICE_ID", "")
    if custom_id:
        _voice_id = custom_id
        print(f"🎤 MiniMax: 使用环境变量音色 {_voice_id}")
        return
    
    if not ref_audio or not os.path.exists(ref_audio):
        print(f"🎤 MiniMax: 参考音频不存在，使用默认音色")
        return
    
    # 从数据库读取已保存的音色映射
    db_key = None
    db_vid = None
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from modules.database import get_conn
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users ORDER BY last_login DESC LIMIT 1")
        row = c.fetchone()
        if row:
            uid = row['user_id']
            c.execute("SELECT value FROM settings WHERE user_id=? AND category='minimax' AND key='voice_map'", (uid,))
            r = c.fetchone()
            if r:
                vm = json.loads(r['value'])
                db_key = vm.get("ref_key")
                db_vid = vm.get("voice_id")
        conn.close()
    except:
        pass
    
    # 用文件路径+修改时间做标识
    ref_key = f"{ref_audio}|{os.path.getmtime(ref_audio):.0f}"
    
    if db_key == ref_key and db_vid:
        _voice_id = db_vid
        print(f"🎤 MiniMax: 音频未变更，使用已有音色 {_voice_id}")
        return
    
    try:
        print("🎤 MiniMax: 检测到新音频，开始上传...")
        file_id = _upload_file(ref_audio)
        if file_id:
            print(f"🎤 MiniMax: 克隆音色中...")
            vid = _clone_voice(file_id)
            if vid:
                voice_map[ref_key] = {"voice_id": vid, "path": ref_audio}
                # 保存到数据库
                try:
                    from modules.database import get_conn
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT user_id FROM users ORDER BY last_login DESC LIMIT 1")
                    row = c.fetchone()
                    if row:
                        uid = row['user_id']
                        val = json.dumps({"ref_key": ref_key, "voice_id": vid})
                        c.execute("DELETE FROM settings WHERE user_id=? AND category='minimax' AND key='voice_map'", (uid,))
                        c.execute("INSERT INTO settings (user_id, category, key, value) VALUES (?, 'minimax', 'voice_map', ?)", (uid, val))
                        conn.commit()
                    conn.close()
                except:
                    pass
                print(f"🎤 MiniMax: 音色克隆成功! voice_id={vid}")
                return
    except Exception as e:
        print(f"🎤 MiniMax: 音色克隆失败: {e}")
    
    print(f"🎤 MiniMax: 使用默认音色 female-shaonv")

def speak(text: str, ref_audio: str = None) -> bool:
    """合成语音并播放"""
    global _voice_id
    key = os.environ.get("MINIMAX_API_KEY", "")
    if not key:
        return False

    try:
        payload = {
            "model": "speech-01",
            "text": text,
            "voice_id": _voice_id,
        }
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
        d, sr = sf.read(tmp)
        sd.play(d, sr)
        sd.wait()
        return True
        
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"MiniMax错误 [{e.code}]: {body[:100]}")
    except Exception as e:
        print(f"MiniMax失败: {e}")
    return False
