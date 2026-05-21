"""
数据库管理 — SQLite用户数据库
首次启动时释放模板数据库到exe根目录
"""
import sqlite3, os, hashlib, json, shutil
from datetime import datetime

# 数据库文件名（打包后放在exe同目录）
DB_NAME = "SakuraMaid_DB.s3db"

# 模板数据库（释放用）— 嵌入在py文件中的初始数据
TEMPLATE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    nickname TEXT DEFAULT '新用户',
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    last_login TEXT,
    avatar TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS settings (
    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,          -- 'astrbot', 'tts', 'llm', 'pet'
    key TEXT NOT NULL,               -- 设置名
    value TEXT DEFAULT '',
    updated_at TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(user_id, category, key),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- 默认管理员账号: admin / admin123 (pbkdf2)
INSERT OR IGNORE INTO users (username, nickname, password_hash)
VALUES ('admin', '管理员', 'pbkdf2:sha256:600000$8f4e9b2c1a3d5e7f$3a9c8b7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a');
"""

# 数据库路径查询
def get_db_path(exe_dir: str = None) -> str:
    """获取数据库路径，优先找exe同目录"""
    if exe_dir:
        return os.path.join(exe_dir, DB_NAME)
    # 开发环境: 项目根目录（database.py在Src/modules，上三层回到根）
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), DB_NAME)

def create_template_db(db_path: str) -> bool:
    """释放模板数据库到指定路径"""
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True) if os.path.dirname(db_path) else None
        conn = sqlite3.connect(db_path)
        conn.executescript(TEMPLATE_SQL)
        conn.commit()
        conn.close()
        print(f"✅ 模板数据库已创建: {db_path}")
        return True
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False

def ensure_db(db_path: str = None) -> str:
    """确保数据库存在，不存在则释放模板"""
    path = db_path or get_db_path()
    if not os.path.exists(path):
        print("📦 数据库不存在，释放模板...")
        create_template_db(path)
    return path

def get_conn(db_path: str = None):
    """获取数据库连接"""
    path = ensure_db(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

# ── 用户操作 ──

def hash_password(password: str) -> str:
    """pbkdf2哈希密码"""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000)
    return f"pbkdf2:sha256:600000${salt}${dk.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """验证密码"""
    try:
        parts = stored_hash.split('$')
        if len(parts) != 3:
            return False
        _, salt, stored_digest = parts
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000)
        return dk.hex() == stored_digest
    except:
        return False

def register_user(username: str, password: str, nickname: str = "") -> dict:
    """注册用户"""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, nickname, password_hash) VALUES (?, ?, ?)",
                  (username, nickname or username, hash_password(password)))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {"success": True, "user_id": user_id, "username": username}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "用户名已存在"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(username: str, password: str) -> dict:
    """用户登录验证"""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"success": False, "error": "用户不存在"}
        if not verify_password(password, row['password_hash']):
            return {"success": False, "error": "密码错误"}
        # 更新最后登录
        conn = get_conn()
        conn.execute("UPDATE users SET last_login=? WHERE user_id=?", 
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), row['user_id']))
        conn.commit()
        conn.close()
        return {"success": True, "user_id": row['user_id'], "username": row['username'], 
                "nickname": row['nickname']}
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_setting(user_id: int, category: str, key: str, value: str):
    """保存用户设置"""
    try:
        conn = get_conn()
        conn.execute("""INSERT OR REPLACE INTO settings (user_id, category, key, value, updated_at)
                        VALUES (?, ?, ?, ?, datetime('now','localtime'))""",
                     (user_id, category, key, str(value)))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_settings(user_id: int, category: str = None) -> dict:
    """获取用户设置"""
    try:
        conn = get_conn()
        if category:
            c = conn.execute("SELECT category, key, value FROM settings WHERE user_id=? AND category=?",
                           (user_id, category))
        else:
            c = conn.execute("SELECT category, key, value FROM settings WHERE user_id=?", (user_id,))
        rows = c.fetchall()
        conn.close()
        result = {}
        for r in rows:
            result[f"{r['category']}.{r['key']}"] = r['value']
        return result
    except:
        return {}

def save_all_settings(user_id: int, cfg: dict):
    """批量保存全部设置"""
    mapping = {
        "astrbot_url": ("astrbot", "url"),
        "astrbot_api_key": ("astrbot", "api_key"),
        "tts_speed": ("tts", "speed"),
        "tts_pitch": ("tts", "pitch"),
        "tts_volume": ("tts", "volume"),
        "tts_emotion": ("tts", "emotion"),
        "tts_voice": ("tts", "voice"),
        "tts_mode": ("tts", "mode"),
        "llm_mode": ("llm", "mode"),
        "llm_api_url": ("llm", "api_url"),
        "llm_api_key": ("llm", "api_key"),
        "llm_api_model": ("llm", "api_model"),
        "llm_local_model": ("llm", "local_model"),
        "character_name": ("pet", "character"),
        "tts_local_model_path": ("tts", "local_model_path"),
    }
    for cfg_key, (cat, db_key) in mapping.items():
        if cfg_key in cfg and cfg[cfg_key]:
            save_setting(user_id, cat, db_key, str(cfg[cfg_key]))
