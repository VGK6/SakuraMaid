"""
技能注册表 — 自我进化系统的数据核心
"""
import os, json, hashlib, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.database import get_conn

class SkillRegistry:
    """技能注册表：CRUD + 匹配 + 评分"""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trigger_keywords TEXT NOT NULL,
                code TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                health_score REAL DEFAULT 70.0,
                env_fingerprint TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS skill_aliases (
                skill_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                FOREIGN KEY(skill_id) REFERENCES skills(id)
            );
            CREATE TABLE IF NOT EXISTS skill_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER,
                success INTEGER NOT NULL,
                duration_ms INTEGER DEFAULT 0,
                error_hash TEXT DEFAULT '',
                env_fingerprint TEXT DEFAULT '',
                timestamp TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(skill_id) REFERENCES skills(id)
            );
            CREATE TABLE IF NOT EXISTS fix_experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_hash TEXT NOT NULL,
                error_template TEXT NOT NULL,
                solution_code TEXT NOT NULL,
                fix_count INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(error_hash, solution_code)
            );
            CREATE INDEX IF NOT EXISTS idx_skills_keywords ON skills(trigger_keywords);
            CREATE INDEX IF NOT EXISTS idx_skill_logs_skill ON skill_logs(skill_id);
            CREATE INDEX IF NOT EXISTS idx_fix_error ON fix_experience(error_hash);
        """)
        conn.commit()
        conn.close()

    # ── 技能CRUD ──

    def register(self, name: str, keywords: list, code: str, priority: int = 0) -> dict:
        """注册新技能"""
        conn = get_conn()
        c = conn.cursor()
        # 检查冲突
        for kw in keywords:
            c.execute("SELECT id, name, version FROM skills WHERE trigger_keywords LIKE ?", (f"%{kw}%",))
            existing = c.fetchone()
            if existing:
                conn.close()
                return {"conflict": True, "skill_id": existing['id'], "name": existing['name'],
                        "version": existing['version'], "message": f"关键词'{kw}'与技能'{existing['name']}'冲突"}
        
        c.execute("""INSERT INTO skills (name, trigger_keywords, code, priority)
                     VALUES (?, ?, ?, ?)""",
                  (name, ','.join(keywords), code, priority))
        sid = c.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "skill_id": sid, "name": name}

    def update(self, skill_id: int, **kwargs):
        """更新技能"""
        conn = get_conn()
        fields = {k: v for k, v in kwargs.items() if k in ['name', 'code', 'priority', 'enabled', 'health_score', 'version']}
        if not fields:
            conn.close()
            return
        fields['updated_at'] = "datetime('now','localtime')"
        sets = ", ".join(f"{k}=?" if k != 'updated_at' else f"{k}={v}" for k, v in fields.items() if k != 'updated_at')
        vals = [v for k, v in fields.items() if k != 'updated_at']
        vals.append(skill_id)
        conn.execute(f"UPDATE skills SET {sets} WHERE id=?", vals)
        conn.commit()
        conn.close()

    def delete(self, skill_id: int):
        conn = get_conn()
        conn.execute("DELETE FROM skills WHERE id=?", (skill_id,))
        conn.execute("DELETE FROM skill_aliases WHERE skill_id=?", (skill_id,))
        conn.commit()
        conn.close()

    def get(self, skill_id: int) -> dict:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM skills WHERE id=?", (skill_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else {}

    def list_all(self, enabled_only: bool = True) -> list:
        conn = get_conn()
        c = conn.cursor()
        q = "SELECT * FROM skills" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY priority DESC, health_score DESC"
        c.execute(q)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    # ── 技能匹配 ──

    def match(self, text: str) -> dict:
        """匹配技能：精确→模糊→无"""
        skills = self.list_all(enabled_only=True)
        if not skills:
            return {}
        
        text_lower = text.lower().strip()
        
        # 1. 精确匹配
        for s in skills:
            kws = [kw.strip().lower() for kw in s['trigger_keywords'].split(',')]
            if text_lower in kws:
                return s
        
        # 2. 模糊匹配（中文字符重叠度）
        best_match, best_score = None, 0
        for s in skills:
            kws_text = s['trigger_keywords'].lower().replace(',', ' ')
            # 中文字符级别的重叠度
            chars = set(text_lower)
            kw_chars = set(kws_text)
            common = len(chars & kw_chars)
            total = len(chars | kw_chars)
            overlap = common / max(total, 1) if total > 0 else 0
            score = overlap * 0.7 + (s['health_score'] / 100) * 0.3
            if score > best_score and score >= 0.4:
                best_score = score
                best_match = s
        
        return best_match or {}

    # ── 日志与评分 ──

    def log(self, skill_id: int, success: bool, duration_ms: int = 0, error: str = ""):
        """记录执行日志"""
        conn = get_conn()
        error_hash = self._normalize_error(error) if error else ""
        conn.execute("""INSERT INTO skill_logs (skill_id, success, duration_ms, error_hash)
                       VALUES (?, ?, ?, ?)""", (skill_id, 1 if success else 0, duration_ms, error_hash))
        conn.commit()
        # 更新健康评分
        self._update_health(skill_id, conn)
        conn.close()

    def _update_health(self, skill_id: int, conn):
        """基于最近100次执行计算健康评分"""
        c = conn.cursor()
        c.execute("""SELECT success, duration_ms FROM skill_logs 
                     WHERE skill_id=? ORDER BY id DESC LIMIT 100""", (skill_id,))
        logs = c.fetchall()
        if not logs:
            return
        total = len(logs)
        successes = sum(1 for l in logs if l['success'])
        avg_duration = sum(l['duration_ms'] for l in logs) / total
        expected = 5000  # 期望5秒内完成
        time_penalty = min(1.0, (avg_duration / expected) - 1) if avg_duration > expected else 0
        health = 100 * (successes / total) * (1 - time_penalty)
        health = max(0, min(100, health))
        c.execute("UPDATE skills SET health_score=? WHERE id=?", (health, skill_id))
        
        # 连续3次失败 → health_score减半
        c.execute("""SELECT success FROM skill_logs WHERE skill_id=? ORDER BY id DESC LIMIT 3""", (skill_id,))
        last3 = [l['success'] for l in c.fetchall()]
        if len(last3) == 3 and not any(last3):
            health = health / 2
            c.execute("UPDATE skills SET health_score=? WHERE id=?", (health, skill_id))
            if health < 20:
                c.execute("UPDATE skills SET enabled=0 WHERE id=?", (skill_id,))
        conn.commit()

    # ── 修复经验库 ──

    def _normalize_error(self, error: str) -> str:
        """错误归一化：替换路径/IP/时间等可变部分"""
        text = error
        text = re.sub(r"'[A-Za-z]:\\\\(?:[^'\\\\]+\\\\)*[^'\\\\]*'", "{path}", text)
        text = re.sub(r"'/[^']+'", "{path}", text)
        text = re.sub(r'\d+\.\d+\.\d+\.\d+', '{ip}', text)
        text = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '{time}', text)
        return hashlib.md5(text.encode()).hexdigest()

    def find_fix(self, error: str) -> dict:
        """查找已知修复方案"""
        error_hash = self._normalize_error(error)
        conn = get_conn()
        c = conn.cursor()
        c.execute("""SELECT * FROM fix_experience WHERE error_hash=? ORDER BY fix_count DESC LIMIT 1""", (error_hash,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else {}

    def save_fix(self, error: str, solution: str):
        """保存修复方案到经验库"""
        error_hash = self._normalize_error(error)
        error_template = re.sub(r"'[^']*'", "{path}", error)[:500]
        conn = get_conn()
        try:
            conn.execute("""INSERT INTO fix_experience (error_hash, error_template, solution_code, fix_count)
                           VALUES (?, ?, ?, 1)""", (error_hash, error_template, solution))
        except:
            conn.execute("""UPDATE fix_experience SET fix_count=fix_count+1, last_used=datetime('now','localtime')
                           WHERE error_hash=? AND solution_code=?""", (error_hash, solution))
        conn.commit()
        conn.close()

    # ── 环境指纹 ──

    def get_fingerprint(self) -> str:
        """获取当前环境指纹"""
        import platform
        fp = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python": platform.python_version(),
        }
        return json.dumps(fp)
