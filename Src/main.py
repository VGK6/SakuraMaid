#!/usr/bin/env python3
"""
樱花庄小女仆 · 桌宠 v2.0
入口点: 数据库检查 → 登录(QDialog) → 自动配置 → 桌宠
"""
import os, sys
from PySide6.QtWidgets import QApplication, QMessageBox

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MaidPet")

    # 数据库
    from modules.database import ensure_db, get_conn
    db_path = ensure_db()
    print(f"📦 数据库就绪: {db_path}")

    # 第一步: 登录 (QDialog, 阻塞直到登录成功或取消)
    from ui.login_ui import LoginUI
    login_ui = LoginUI()
    if login_ui.exec() != LoginUI.Accepted:
        print("用户取消登录，退出")
        return

    user = login_ui.user_info
    print(f"✅ 登录成功: {user['username']} (user_id={user['user_id']})")

    # 第二步: 设置读取 + 选择修改
    from ui.config_ui import db_to_cfg
    cfg = db_to_cfg(user['user_id'])
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM settings WHERE user_id=?", (user['user_id'],))
    setting_count = c.fetchone()[0]
    conn.close()
    is_new = setting_count == 0

    should_configure = False
    if is_new:
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
        from ui.config_ui import ConfigUI
        cfg_ui = ConfigUI(user=user)
        if cfg_ui.exec() == ConfigUI.Accepted:
            cfg = cfg_ui.cfg
            print("✅ 配置已保存")
        else:
            print("用户取消配置，使用已有配置")

    # 第三步: 启动桌宠
    from core.pet_window import MaidPet
    pet = MaidPet(cfg)
    print("🌸 桌宠启动完成")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
