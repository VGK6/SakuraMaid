"""
配置UI — 左侧导航 + 右侧内容面板
"""
import os, json, sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
                               QLineEdit, QComboBox, QPushButton, QSlider, QCheckBox,
                               QGroupBox, QFormLayout, QFileDialog, QListWidget, QListWidgetItem,
                               QFrame, QSpinBox, QRadioButton)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pet_config.json")

DEFAULT_CFG = {
    "astrbot_api_key": "abk_pHR4OJsje0xanu0dXxSEGqATFZY_eUNmfPbNyed5EkQ",
    "astrbot_url": "http://127.0.0.1:6185",
    "username": "龙之介大人",
    "tts_enabled": True,
    "tts_voice": "edge-tts",
    "character_name": "小女仆",
    "sound_source": "",
    "tts_speed": 1.0,
    "tts_pitch": 0.0,
    "tts_volume": 80,
    "tts_emotion": "平静",
    "llm_mode": "api",
    "llm_provider": "OpenAI",
    "llm_api_url": "https://api.deepseek.com/v1/chat/completions",
    "llm_api_key": "",
    "llm_model": "deepseek-v4-flash",
    "llm_local_framework": "llama.cpp",
    "llm_local_model": "",
    "llm_context": 4096,
    "llm_device": "CPU",
    "tts_mode": "local",
    "tts_local_model_path": "",
    "tts_local_device": "CPU",
    "tts_api_provider": "OpenAI TTS",
    "tts_api_url": "",
    "tts_api_key": "",
    "tts_api_model": "tts-1",
    "window_x": -1, "window_y": -1,
    "auto_start": False,
}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CFG, **json.load(f)}
        except:
            pass
    return dict(DEFAULT_CFG)

def save_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class NavButton(QPushButton):
    def __init__(self, icon, text, page_idx):
        super().__init__(f"  {icon}  {text}")
        self.page_idx = page_idx
        self.setCheckable(True)
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton { text-align: left; padding: 10px 15px; border: none; 
                         font-size: 14px; color: #666; border-radius: 8px; margin: 2px 8px; background: transparent; }
            QPushButton:checked, QPushButton:hover { background: #ff6b81; color: white; }
        """)


class ConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.accepted = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("AI 桌宠配置面板")
        self.resize(900, 680)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget { font-family: Microsoft YaHei; font-size: 13px; background: #fafafa; }
            QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 8px; 
                       margin-top: 10px; padding: 15px; background: white; }
            QGroupBox::title { color: #ff6b81; subcontrol-origin: margin; left: 12px; font-size: 13px; }
            QLineEdit, QComboBox { padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; 
                                  background: white; font-size: 13px; }
            QPushButton { padding: 8px 16px; border-radius: 4px; font-size: 13px; 
                         background: #f0f0f0; border: 1px solid #ddd; }
            QPushButton:hover { background: #ff6b81; color: white; border-color: #ff6b81; }
            QSlider::groove:horizontal { height: 6px; background: #ddd; border-radius: 3px; }
            QSlider::handle:horizontal { background: #ff6b81; width: 16px; height: 16px; 
                                        margin: -5px 0; border-radius: 8px; }
            QRadioButton { spacing: 8px; font-size: 13px; }
            QRadioButton::indicator { width: 18px; height: 18px; border-radius: 3px; border: 2px solid #ccc; background: white; }
            QRadioButton::indicator:checked { background: #4CAF50; border-color: #4CAF50; }
            QRadioButton::indicator:hover { border-color: #999; }
            QCheckBox { spacing: 8px; font-size: 13px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 3px; border: 2px solid #ccc; background: white; }
            QCheckBox::indicator:checked { background: #4CAF50; border-color: #4CAF50; }
            QCheckBox::indicator:hover { border-color: #999; }
            QSpinBox { padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
        """)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ====== 左侧导航 ======
        nav_panel = QFrame()
        nav_panel.setFixedWidth(180)
        nav_panel.setStyleSheet("background: #fef6f7; border-right: 1px solid #ffd6dc;")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 10, 0, 10)
        nav_layout.setSpacing(4)

        # 标题
        title = QLabel("🌸 桌宠配置")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Microsoft YaHei', 15, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 10px 0 20px 0;")
        nav_layout.addWidget(title)

        # 导航按钮
        self.nav_btns = []
        nav_items = [("🖼️", "桌宠设置", 0), ("⚙️", "系统配置", 1)]
        self.stacked = QStackedWidget()

        for icon, text, idx in nav_items:
            btn = NavButton(icon, text, idx)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self.nav_btns.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        # 版本
        ver = QLabel("v2.0")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #ccc; font-size: 11px; padding: 10px;")
        nav_layout.addWidget(ver)

        # ====== 右侧内容 ======
        content_panel = QFrame()
        content_panel.setStyleSheet("background: #fafafa;")
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(20, 15, 20, 15)

        # 页面1: 桌宠设置
        page0 = self._build_pet_page()
        self.stacked.addWidget(page0)

        # 页面2: 系统配置
        page1 = self._build_system_page()
        self.stacked.addWidget(page1)

        content_layout.addWidget(self.stacked)

        # 底部按钮
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.save_btn = QPushButton("✅ 保存")
        self.save_btn.setStyleSheet("background: #ff6b81; color: white; font-size: 14px; padding: 10px 30px; border: none; border-radius: 6px;")
        self.save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        btn_bar.addWidget(self.save_btn)
        btn_bar.addWidget(cancel_btn)
        content_layout.addLayout(btn_bar)

        main_layout.addWidget(nav_panel)
        main_layout.addWidget(content_panel, 1)
        self.setLayout(main_layout)

        # 默认选中第一个
        self.nav_btns[0].setChecked(True)

    def _switch_page(self, idx):
        for btn in self.nav_btns:
            btn.setChecked(btn.page_idx == idx)
        self.stacked.setCurrentIndex(idx)

    # ── 页面1: 桌宠设置 ──
    def _build_pet_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        # 标题
        title = QLabel("桌宠设置")
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 5px 0;")
        layout.addWidget(title)

        # 参考图
        g1 = QGroupBox("桌宠参考图")
        g1_layout = QHBoxLayout()
        preview = QLabel()
        preview.setFixedSize(140, 140)
        preview.setStyleSheet("border: 2px dashed #ddd; border-radius: 8px; background: #f5f5f5;")
        preview.setAlignment(Qt.AlignCenter)
        preview.setText("预览图")
        self.char_preview = preview
        btn_col = QVBoxLayout()
        self.upload_btn = QPushButton("📁 上传图片")
        self.upload_btn.clicked.connect(self._pick_image)
        self.reset_btn = QPushButton("🔄 重置默认")
        self.reset_btn.setStyleSheet("background: #f0f0f0;")
        fmt_label = QLabel("支持格式: PNG, JPG, GIF\n建议尺寸: 256x256")
        fmt_label.setStyleSheet("color: #999; font-size: 11px;")
        btn_col.addWidget(self.upload_btn)
        btn_col.addWidget(self.reset_btn)
        btn_col.addWidget(fmt_label)
        btn_col.addStretch()
        g1_layout.addWidget(preview)
        g1_layout.addLayout(btn_col)
        g1.setLayout(g1_layout)
        layout.addWidget(g1)

        # 参考音色参数
        g2 = QGroupBox("参考音色参数")
        g2_layout = QFormLayout()
        g2_layout.setSpacing(10)

        self.tts_model_combo = QComboBox()
        self.tts_model_combo.addItems(["默认女声", "默认男声", "自定义"])
        g2_layout.addRow("音色模型:", self.tts_model_combo)

        # 语速
        speed_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(int(self.cfg.get("tts_speed", 1.0) * 100))
        self.speed_label = QLabel(f"{self.cfg.get('tts_speed', 1.0):.1f}x")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"{v/100:.1f}x"))
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_label)
        g2_layout.addRow("语速:", speed_row)

        # 音调
        pitch_row = QHBoxLayout()
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(int(self.cfg.get("tts_pitch", 0.0)))
        self.pitch_label = QLabel(f"{self.cfg.get('tts_pitch', 0.0):+.1f}")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(f"{v:+d}"))
        pitch_row.addWidget(self.pitch_slider)
        pitch_row.addWidget(self.pitch_label)
        g2_layout.addRow("音调:", pitch_row)

        # 音量
        vol_row = QHBoxLayout()
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.cfg.get("tts_volume", 80))
        self.vol_label = QLabel(f"{self.cfg.get('tts_volume', 80)}%")
        self.vol_slider.valueChanged.connect(lambda v: self.vol_label.setText(f"{v}%"))
        vol_row.addWidget(self.vol_slider)
        vol_row.addWidget(self.vol_label)
        g2_layout.addRow("音量:", vol_row)

        # 情感
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["平静", "开心", "悲伤", "鼓励"])
        self.emotion_combo.setCurrentText(self.cfg.get("tts_emotion", "平静"))
        g2_layout.addRow("情感:", self.emotion_combo)

        btn_row = QHBoxLayout()
        self.test_btn = QPushButton("🎧 试听示例")
        self.save_preset_btn = QPushButton("💾 保存为预设")
        btn_row.addWidget(self.test_btn)
        btn_row.addWidget(self.save_preset_btn)
        btn_row.addStretch()
        g2_layout.addRow("", btn_row)
        g2.setLayout(g2_layout)
        layout.addWidget(g2)

        layout.addStretch()
        return page

    # ── 页面2: 系统配置 ──
    def _build_system_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("系统配置")
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 5px 0;")
        layout.addWidget(title)

        # AstrBot API
        g1 = QGroupBox("AstrBot API 设置")
        g1_layout = QFormLayout()
        g1_layout.setSpacing(8)
        self.api_enable = QCheckBox("启用 API")
        self.api_enable.setChecked(True)
        self.api_url = QLineEdit(self.cfg.get("astrbot_url", "http://127.0.0.1:6185"))
        self.api_key = QLineEdit(self.cfg.get("astrbot_api_key", ""))
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_show_btn = QPushButton("显示")
        self.api_show_btn.setFixedWidth(50)
        self.api_show_btn.clicked.connect(lambda: self.api_key.setEchoMode(QLineEdit.Normal if self.api_key.echoMode() else QLineEdit.Password))
        api_key_row = QHBoxLayout()
        api_key_row.addWidget(self.api_key)
        api_key_row.addWidget(self.api_show_btn)
        self.api_timeout = QSpinBox()
        self.api_timeout.setRange(5, 120)
        self.api_timeout.setValue(30)
        self.test_api_btn = QPushButton("🔗 测试连接")
        self.test_api_btn.clicked.connect(self._test_api)
        g1_layout.addRow("", self.api_enable)
        g1_layout.addRow("API 地址:", self.api_url)
        g1_layout.addRow("API Key:", api_key_row)
        g1_layout.addRow("超时时间:", self.api_timeout)
        g1_layout.addRow("", self.test_api_btn)
        g1.setLayout(g1_layout)
        layout.addWidget(g1)

        # TTS
        g2 = QGroupBox("TTS 模型设置")
        g2_layout = QVBoxLayout()
        # 模式选择
        mode_row = QHBoxLayout()
        self.tts_local_radio = QRadioButton("本地")
        self.tts_api_radio = QRadioButton("API")
        if self.cfg.get("tts_mode") == "local":
            self.tts_local_radio.setChecked(True)
        else:
            self.tts_api_radio.setChecked(True)
        mode_row.addWidget(QLabel("模式:"))
        mode_row.addWidget(self.tts_local_radio)
        mode_row.addWidget(self.tts_api_radio)
        mode_row.addStretch()
        g2_layout.addLayout(mode_row)

        self.tts_local_widget = QWidget()
        tts_local = QFormLayout(self.tts_local_widget)
        self.tts_local_path = QLineEdit(self.cfg.get("tts_local_model_path", ""))
        self.tts_local_browse = QPushButton("浏览")
        tts_local_path_row = QHBoxLayout()
        tts_local_path_row.addWidget(self.tts_local_path)
        tts_local_path_row.addWidget(self.tts_local_browse)
        tts_local.addRow("模型路径:", tts_local_path_row)
        self.tts_local_device = QComboBox()
        self.tts_local_device.addItems(["CPU", "CUDA"])
        self.tts_local_device.setCurrentText(self.cfg.get("tts_local_device", "CPU"))
        tts_local.addRow("设备:", self.tts_local_device)
        g2_layout.addWidget(self.tts_local_widget)

        self.tts_api_widget = QWidget()
        tts_api = QFormLayout(self.tts_api_widget)
        self.tts_api_provider = QComboBox()
        self.tts_api_provider.addItems(["OpenAI TTS", "Edge TTS"])
        tts_api.addRow("Provider:", self.tts_api_provider)
        self.tts_api_url = QLineEdit(self.cfg.get("tts_api_url", ""))
        tts_api.addRow("API URL:", self.tts_api_url)
        self.tts_api_key = QLineEdit(self.cfg.get("tts_api_key", ""))
        tts_api.addRow("API Key:", self.tts_api_key)
        self.tts_api_model = QLineEdit(self.cfg.get("tts_api_model", "tts-1"))
        tts_api.addRow("模型名:", self.tts_api_model)
        g2_layout.addWidget(self.tts_api_widget)

        self.tts_local_radio.toggled.connect(lambda: self.tts_local_widget.setVisible(self.tts_local_radio.isChecked()))
        self.tts_api_radio.toggled.connect(lambda: self.tts_api_widget.setVisible(self.tts_api_radio.isChecked()))
        self.tts_api_widget.setVisible(self.tts_api_radio.isChecked())
        self.tts_local_widget.setVisible(self.tts_local_radio.isChecked())

        g2.setLayout(g2_layout)
        layout.addWidget(g2)

        # LLM
        g3 = QGroupBox("LLM 模型设置")
        g3_layout = QVBoxLayout()
        llm_mode_row = QHBoxLayout()
        self.llm_local_radio = QRadioButton("本地")
        self.llm_api_radio = QRadioButton("API")
        if self.cfg.get("llm_mode") == "local":
            self.llm_local_radio.setChecked(True)
        else:
            self.llm_api_radio.setChecked(True)
        llm_mode_row.addWidget(QLabel("模式:"))
        llm_mode_row.addWidget(self.llm_local_radio)
        llm_mode_row.addWidget(self.llm_api_radio)
        llm_mode_row.addStretch()
        g3_layout.addLayout(llm_mode_row)

        self.llm_local_widget = QWidget()
        llm_local = QFormLayout(self.llm_local_widget)
        self.llm_framework = QComboBox()
        self.llm_framework.addItems(["llama.cpp", "Ollama", "llama-cpp-python"])
        llm_local.addRow("后端框架:", self.llm_framework)
        self.llm_local_model = QLineEdit(self.cfg.get("llm_local_model", ""))
        self.llm_local_browse = QPushButton("浏览")
        llm_local_path = QHBoxLayout()
        llm_local_path.addWidget(self.llm_local_model)
        llm_local_path.addWidget(self.llm_local_browse)
        llm_local.addRow("模型路径:", llm_local_path)
        self.llm_context = QSpinBox()
        self.llm_context.setRange(1024, 32768)
        self.llm_context.setValue(self.cfg.get("llm_context", 4096))
        self.llm_context.setSingleStep(1024)
        llm_local.addRow("上下文长度:", self.llm_context)
        self.llm_device = QComboBox()
        self.llm_device.addItems(["CPU", "CUDA"])
        llm_local.addRow("推理设备:", self.llm_device)
        g3_layout.addWidget(self.llm_local_widget)

        self.llm_api_widget = QWidget()
        llm_api = QFormLayout(self.llm_api_widget)
        self.llm_api_provider = QComboBox()
        self.llm_api_provider.addItems(["OpenAI", "DeepSeek", "Ollama"])
        llm_api.addRow("Provider:", self.llm_api_provider)
        self.llm_api_url = QLineEdit(self.cfg.get("llm_api_url", ""))
        llm_api.addRow("API URL:", self.llm_api_url)
        self.llm_api_key = QLineEdit(self.cfg.get("llm_api_key", ""))
        llm_api.addRow("API Key:", self.llm_api_key)
        self.llm_api_model = QLineEdit(self.cfg.get("llm_api_model", ""))
        llm_api.addRow("模型名:", self.llm_api_model)
        g3_layout.addWidget(self.llm_api_widget)

        self.llm_local_radio.toggled.connect(lambda: self.llm_local_widget.setVisible(self.llm_local_radio.isChecked()))
        self.llm_api_radio.toggled.connect(lambda: self.llm_api_widget.setVisible(self.llm_api_radio.isChecked()))
        self.llm_api_widget.setVisible(self.llm_api_radio.isChecked())
        self.llm_local_widget.setVisible(self.llm_local_radio.isChecked())

        g3.setLayout(g3_layout)
        layout.addWidget(g3)

        layout.addStretch()
        return page

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择桌宠参考图", "", "图片 (*.png *.jpg *.gif)")
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                self.char_preview.setPixmap(pix.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.char_preview.setText("")

    def _test_api(self):
        import urllib.request
        try:
            key = self.api_key.text().strip()
            url = self.api_url.text().strip()
            data = json.dumps({"message": "ping", "session_id": "_test"}).encode()
            req = urllib.request.Request(f"{url}/api/v1/chat", data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "连接成功", f"AstrBot API 连接成功!\n状态码: {resp.status}")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "连接失败", f"无法连接 AstrBot:\n{str(e)[:60]}")

    def _on_save(self):
        self.cfg = {
            "astrbot_api_key": self.api_key.text().strip(),
            "astrbot_url": self.api_url.text().strip(),
            "username": "龙之介大人",
            "tts_enabled": True,
            "tts_voice": self.tts_model_combo.currentText(),
            "tts_speed": self.speed_slider.value() / 100,
            "tts_pitch": float(self.pitch_slider.value()),
            "tts_volume": self.vol_slider.value(),
            "tts_emotion": self.emotion_combo.currentText(),
            "tts_mode": "local" if self.tts_local_radio.isChecked() else "api",
            "tts_local_model_path": self.tts_local_path.text().strip(),
            "tts_local_device": self.tts_local_device.currentText(),
            "tts_api_provider": self.tts_api_provider.currentText(),
            "tts_api_url": self.tts_api_url.text().strip(),
            "tts_api_key": self.tts_api_key.text().strip(),
            "tts_api_model": self.tts_api_model.text().strip(),
            "llm_mode": "local" if self.llm_local_radio.isChecked() else "api",
            "llm_framework": self.llm_framework.currentText(),
            "llm_local_model": self.llm_local_model.text().strip(),
            "llm_context": self.llm_context.value(),
            "llm_device": self.llm_device.currentText(),
            "llm_api_provider": self.llm_api_provider.currentText(),
            "llm_api_url": self.llm_api_url.text().strip(),
            "llm_api_key": self.llm_api_key.text().strip(),
            "llm_api_model": self.llm_api_model.text().strip(),
            "character_name": "小女仆",
            "window_x": -1, "window_y": -1,
            "auto_start": False,
        }
        save_config(self.cfg)
        self.accepted = True
        self.close()
