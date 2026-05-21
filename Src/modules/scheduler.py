"""
日程与提醒 - 读取AstrBot定时任务 + IMAP邮件
"""
import sqlite3, imaplib, email, os, json
from datetime import datetime

ASTROB_DB = os.path.expanduser("~") + "/.astrbot/data/data_v4.db"

def get_schedule() -> list:
    """获取AstrBot中的定时任务列表"""
    try:
        conn = sqlite3.connect(ASTROB_DB)
        c = conn.cursor()
        c.execute("SELECT name, cron_expression, next_run_time FROM cron_jobs WHERE enabled=1")
        rows = c.fetchall()
        conn.close()
        results = []
        for name, cron, next_time in rows:
            # 过滤掉自我进化的内部任务
            if 'SelfEvolution' in name:
                continue
            results.append({"name": name, "cron": cron, "next": str(next_time or "")})
        return results
    except:
        return []

def get_unread_mail() -> list:
    """检查QQ邮箱未读邮件"""
    try:
        cfg_path = os.path.expanduser("~") + "/.astrbot/plugin_data/astrbot_plugin_mail/data.json"
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            cfg_path2 = os.path.expanduser("~") + "/.astrbot/plugin_data/astrbot_plugin_mail/config.json"
            with open(cfg_path2, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            accts = cfg.get('mail_accounts', [])
            if not accts:
                return []
            acct = accts[0]
            conn = imaplib.IMAP4_SSL(acct.get('imap_server', 'imap.qq.com'), 
                                       acct.get('imap_port', 993), timeout=10)
            conn.login(acct['email'], acct['password'])
            conn.select("INBOX")
            _, data = conn.search(None, "UNSEEN")
            mids = data[0].split() if data[0] else []
            mails = []
            for mid in mids[-5:]:
                _, msg_data = conn.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                mails.append({"subject": msg['Subject'] or "", "from": msg['From'] or ""})
            conn.logout()
            return mails
        return []
    except:
        return []
