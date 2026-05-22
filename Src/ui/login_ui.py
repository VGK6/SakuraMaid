"""
登录UI — 用户注册/登录界面
支持"记住我"和"直接登录"
"""
import os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from modules.database import login_user, register_user

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QCheckBox,
                               QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

SESSION_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session.json")


def save_session(username: str, password: str = "", direct_login: bool = False):
    data = {"username": username, "password": password, "direct_login": direct_login}
    with open(SESSION_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def load_session() -> dict:
    if os.path.exists(SESSION_PATH):
        try:
            with open(SESSION_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def clear_session():
    if os.path.exists(SESSION_PATH):
        os.remove(SESSION_PATH)


class LoginUI(QDialog):
    def __init__(self):
        super().__init__()
        self.user_info = None
        self.direct_login = False
        self._init_ui()
        self._check_session()

    def _init_ui(self):
        self.setWindowTitle("🌸 樱花庄小女仆 · 登录")
        self.resize(420, 560)
        self.setMinimumSize(360, 480)
        self.setStyleSheet("""
            QWidget { background: #fef6f7; font-family: Microsoft YaHei; }
            QLineEdit { padding: 22px 20px; border: 1px solid #ffb6c1; border-radius: 8px; 
                       background: white; font-size: 16px; min-height: 40px; }
            QPushButton { padding: 14px; border-radius: 8px; font-size: 15px; font-weight: bold; }
            QCheckBox { spacing: 8px; font-size: 14px; color: #666; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(40, 25, 40, 25)

        icon = QLabel("🌸")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont('Microsoft YaHei', 48))
        layout.addWidget(icon)

        title = QLabel("樱花庄小女仆")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Microsoft YaHei', 20, QFont.Bold))
        title.setStyleSheet("color: #ff6b81;")
        layout.addWidget(title)

        sub = QLabel("请登录以继续")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #999; font-size: 13px; padding-bottom: 8px;")
        layout.addWidget(sub)

        form = QFrame()
        form.setStyleSheet("background: white; border-radius: 12px; padding: 15px;")
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        form_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._do_login)
        form_layout.addWidget(self.password_input)

        # 记住我 + 直接登录
        options_row = QHBoxLayout()
        self.remember_cb = QCheckBox("记住我")
        self.direct_cb = QCheckBox("直接登录")
        self.direct_cb.setStyleSheet("color: #ff6b81;")
        options_row.addWidget(self.remember_cb)
        options_row.addWidget(self.direct_cb)
        options_row.addStretch()
        form_layout.addLayout(options_row)

        layout.addWidget(form)

        self.login_btn = QPushButton("登 录")
        self.login_btn.setStyleSheet("background: #ff6b81; color: white; font-size: 16px; "
                                     "padding: 16px; border-radius: 10px;")
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        self.switch_btn = QPushButton("没有账号？点此注册")
        self.switch_btn.setStyleSheet("background: transparent; color: #ff6b81; border: none; font-size: 13px;")
        self.switch_btn.clicked.connect(self._switch_mode)
        layout.addWidget(self.switch_btn)

        self.is_register = False
        layout.addStretch()

        ver = QLabel("v2.0")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #ccc; font-size: 11px;")
        layout.addWidget(ver)

        self.setLayout(layout)

    def _check_session(self):
        """检查是否有保存的会话"""
        session = load_session()
        if session.get("username"):
            self.username_input.setText(session["username"])
            self.remember_cb.setChecked(True)
            # 记住我：自动填密码
            if session.get("password"):
                self.password_input.setText(session["password"])
            if session.get("direct_login"):
                self.direct_cb.setChecked(True)
                # 直接登录：自动登录
                self._do_auto_login(session["username"])

    def _do_auto_login(self, username):
        """使用记住的会话自动登录"""
        from modules.database import get_conn
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            self.user_info = {"user_id": row['user_id'], "username": row['username'],
                            "nickname": row['nickname']}
            self.direct_login = True
            self.accept()

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return

        if self.is_register:
            result = register_user(username, password)
            if result['success']:
                QMessageBox.information(self, "注册成功", f"用户 {username} 注册成功！请登录")
                self._switch_mode()
            else:
                QMessageBox.warning(self, "注册失败", result.get('error', '未知错误'))
        else:
            result = login_user(username, password)
            if result['success']:
                self.user_info = result
                self.direct_login = self.direct_cb.isChecked()
                if self.remember_cb.isChecked():
                    save_session(username, password, self.direct_cb.isChecked())
                self.accept()
            else:
                QMessageBox.warning(self, "登录失败", result.get('error', '未知错误'))

    def _switch_mode(self):
        self.is_register = not self.is_register
        if self.is_register:
            self.login_btn.setText("注 册")
            self.switch_btn.setText("已有账号？点此登录")
            self.remember_cb.hide()
            self.direct_cb.hide()
        else:
            self.login_btn.setText("登 录")
            self.switch_btn.setText("没有账号？点此注册")
            self.remember_cb.show()
            self.direct_cb.show()
