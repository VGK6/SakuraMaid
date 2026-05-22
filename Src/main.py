#!/usr/bin/env python3
"""
樱花庄小女仆 · 桌宠 v2.0
入口点: 数据库检查 → 登录(记住我/直接登录) → 配置/直接启动
"""
import os, sys
from PySide6.QtWidgets import QApplication, QMessageBox

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MaidPet")

    # 数据库
    from modules.database import ensure_db
    db_path = ensure_db()
    print(f"📦 数据库就绪: {db_path}")

    # 第一步: 登录
    from ui.login_ui import LoginUI, load_session, clear_session
    session = load_session()

    login_ui = LoginUI()

    # 如果是直接登录模式，直接跳过
    if session.get("direct_login") and session.get("username"):
        from modules.database import get_conn
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (session["username"],))
        row = c.fetchone()
        conn.close()
        if row:
            login_ui.user_info = {"user_id": row['user_id'], "username": row['username'],
                                 "nickname": row['nickname']}
            login_ui.direct_login = True
            print(f"✅ 自动登录: {row['username']}")
        else:
            clear_session()
            if login_ui.exec() != LoginUI.Accepted:
                print("用户取消登录，退出")
                return
    else:
        if login_ui.exec() != LoginUI.Accepted:
            print("用户取消登录，退出")
            return

    user = login_ui.user_info
    print(f"✅ 登录成功: {user['username']} (user_id={user['user_id']})")

    # 第二步: 配置
    from ui.config_ui import db_to_cfg, ConfigUI
    from modules.database import get_conn

    cfg = db_to_cfg(user['user_id'])

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM settings WHERE user_id=?", (user['user_id'],))
    setting_count = c.fetchone()[0]
    conn.close()
    is_new = setting_count == 0

    should_configure = True
    if not is_new and login_ui.direct_login:
        should_configure = False
    elif is_new:
        reply = QMessageBox.information(None, "新用户",
            f"欢迎 {user.get('nickname', user['username'])}！\n是否进入配置页面？",
            QMessageBox.Yes | QMessageBox.No)
        should_configure = (reply == QMessageBox.Yes)
    else:
        reply = QMessageBox.question(None, "配置",
            "是否修改配置？",
            QMessageBox.Yes | QMessageBox.No)
        should_configure = (reply == QMessageBox.Yes)

    if should_configure:
        cfg_ui = ConfigUI(user=user)
        if cfg_ui.exec() == ConfigUI.Accepted:
            if cfg_ui.skip_cfg_cb.isChecked():
                # 记住跳过选择
                from ui.login_ui import save_session
                save_session(user['username'], "", direct_login=True)
            cfg = cfg_ui.cfg
            print("✅ 配置已保存")

    # 第三步: 启动桌宠
    from core.pet_window import MaidPet
    pet = MaidPet(cfg)
    print("🌸 桌宠启动完成")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
