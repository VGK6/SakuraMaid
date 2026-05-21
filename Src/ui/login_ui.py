"""
登录UI — 用户注册/登录界面
"""
import sys, os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox,
                               QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from modules.database import login_user, register_user


class LoginUI(QDialog):
    def __init__(self):
        super().__init__()
        self.user_info = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("🌸 樱花庄小女仆 · 登录")
        self.resize(420, 520)
        self.setMinimumSize(360, 440)
        self.setStyleSheet("""
            QWidget { background: #fef6f7; font-family: Microsoft YaHei; }
            QLineEdit { padding: 22px 20px; border: 1px solid #ffb6c1; border-radius: 8px; 
                       background: white; font-size: 16px; min-height: 40px; }
            QPushButton { padding: 12px; border-radius: 8px; font-size: 14px; font-weight: bold; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        # 标题
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
        sub.setStyleSheet("color: #999; font-size: 13px; padding-bottom: 10px;")
        layout.addWidget(sub)

        # 表单
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

        layout.addWidget(form)

        # 按钮
        self.login_btn = QPushButton("登 录")
        self.login_btn.setStyleSheet("background: #ff6b81; color: white; font-size: 16px; "
                                     "padding: 14px; border-radius: 10px;")
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        # 注册切换
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
                self.accept()
            else:
                QMessageBox.warning(self, "登录失败", result.get('error', '未知错误'))

    def _switch_mode(self):
        self.is_register = not self.is_register
        if self.is_register:
            self.login_btn.setText("注 册")
            self.switch_btn.setText("已有账号？点此登录")
        else:
            self.login_btn.setText("登 录")
            self.switch_btn.setText("没有账号？点此注册")
