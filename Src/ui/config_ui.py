"""
配置UI — 左侧导航 + 右侧内容面板
所有配置读写走数据库
"""
import os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from modules.database import get_settings, save_setting

from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
                               QLineEdit, QComboBox, QPushButton, QSlider, QCheckBox,
                               QGroupBox, QFormLayout, QFileDialog, QFrame,
                               QSpinBox, QRadioButton, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap


def db_to_cfg(user_id: int) -> dict:
    """从数据库读取全部配置"""
    raw = get_settings(user_id)
    
    def g(key, default=""):
        val = raw.get(key, "")
        return val if val != "" else default
    
    out = {
        "astrbot_url": g("astrbot.url", "http://127.0.0.1:6185"),
        "astrbot_api_key": g("astrbot.api_key", ""),
        "tts_speed": float(g("tts.speed", "1.0")),
        "tts_pitch": float(g("tts.pitch", "0")),
        "tts_volume": int(float(g("tts.volume", "80"))),
        "tts_emotion": g("tts.emotion", "平静"),
        "tts_voice": g("tts.voice", "默认女声"),
        "tts_mode": g("tts.mode", "api"),
        "tts_local_model_path": g("tts.local_model_path", ""),
        "tts_local_device": g("tts.local_device", "CPU"),
        "tts_api_provider": g("tts.api_provider", "OpenAI TTS"),
        "tts_api_url": g("tts.api_url", ""),
        "tts_api_key": g("tts.api_key", ""),
        "tts_api_model": g("tts.api_model", "tts-1"),
        "llm_mode": g("llm.mode", "api"),
        "llm_framework": g("llm.framework", "llama.cpp"),
        "llm_local_model": g("llm.local_model", ""),
        "llm_context": int(g("llm.context", "4096")),
        "llm_device": g("llm.device", "CPU"),
        "llm_api_provider": g("llm.api_provider", "OpenAI"),
        "llm_api_url": g("llm.api_url", ""),
        "llm_api_key": g("llm.api_key", ""),
        "llm_api_model": g("llm.api_model", ""),
        "character_name": g("pet.character", "小女仆"),
        "sound_source": g("pet.sound_source", ""),
        "window_x": int(g("window_x", "-1")),
        "window_y": int(g("window_y", "-1")),
    }
    return out


def cfg_to_db(user_id: int, cfg: dict):
    """保存全部配置到数据库"""
    mapping = [
        ("astrbot", "url", cfg.get("astrbot_url", "")),
        ("astrbot", "api_key", cfg.get("astrbot_api_key", "")),
        ("tts", "speed", str(cfg.get("tts_speed", 1.0))),
        ("tts", "pitch", str(cfg.get("tts_pitch", 0.0))),
        ("tts", "volume", str(cfg.get("tts_volume", 80))),
        ("tts", "emotion", cfg.get("tts_emotion", "平静")),
        ("tts", "voice", cfg.get("tts_voice", "默认女声")),
        ("tts", "mode", cfg.get("tts_mode", "api")),
        ("tts", "local_model_path", cfg.get("tts_local_model_path", "")),
        ("tts", "local_device", cfg.get("tts_local_device", "CPU")),
        ("tts", "api_provider", cfg.get("tts_api_provider", "OpenAI TTS")),
        ("tts", "api_url", cfg.get("tts_api_url", "")),
        ("tts", "api_key", cfg.get("tts_api_key", "")),
        ("tts", "api_model", cfg.get("tts_api_model", "tts-1")),
        ("llm", "mode", cfg.get("llm_mode", "api")),
        ("llm", "framework", cfg.get("llm_framework", "llama.cpp")),
        ("llm", "local_model", cfg.get("llm_local_model", "")),
        ("llm", "context", str(cfg.get("llm_context", 4096))),
        ("llm", "device", cfg.get("llm_device", "CPU")),
        ("llm", "api_provider", cfg.get("llm_api_provider", "OpenAI")),
        ("llm", "api_url", cfg.get("llm_api_url", "")),
        ("llm", "api_key", cfg.get("llm_api_key", "")),
        ("llm", "api_model", cfg.get("llm_api_model", "")),
        ("pet", "character", cfg.get("character_name", "小女仆")),
        ("pet", "sound_source", cfg.get("sound_source", "")),
    ]
    for cat, key, val in mapping:
        save_setting(user_id, cat, key, val)


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


class ConfigUI(QDialog):
    def __init__(self, user: dict = None):
        super().__init__()
        self.user = user or {}
        self.cfg = db_to_cfg(self.user.get('user_id', 0))
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
            QLineEdit, QComboBox { padding: 15px 14px; border: 1px solid #ddd; border-radius: 4px; 
                                  background: white; font-size: 14px; min-height: 32px; }
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

        title = QLabel("🌸 桌宠配置")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Microsoft YaHei', 15, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 10px 0 5px 0;")
        nav_layout.addWidget(title)

        # 用户信息 + 登出
        if self.user:
            user_btn = QPushButton(f"👤 {self.user.get('nickname', self.user.get('username',''))}  ▼")
            user_btn.setStyleSheet("text-align: center; padding: 8px; border: none; color: #999; font-size: 12px; background: transparent;")
            user_btn.clicked.connect(self._logout)
            nav_layout.addWidget(user_btn)

        self.nav_btns = []
        nav_items = [("🖼️", "桌宠设置", 0), ("⚙️", "系统配置", 1)]
        self.stacked = QStackedWidget()

        for icon, text, idx in nav_items:
            btn = NavButton(icon, text, idx)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self.nav_btns.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        ver = QLabel("v2.0")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #ccc; font-size: 11px; padding: 10px;")
        nav_layout.addWidget(ver)

        # ====== 右侧内容 ======
        content_panel = QFrame()
        content_panel.setStyleSheet("background: #fafafa;")
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(20, 15, 20, 15)

        page0 = self._build_pet_page()
        self.stacked.addWidget(page0)
        page1 = self._build_system_page()
        self.stacked.addWidget(page1)

        content_layout.addWidget(self.stacked)

        # 跳过配置 + 按钮
        btn_bar = QHBoxLayout()
        self.skip_cfg_cb = QCheckBox("跳过配置，直接启动")
        self.skip_cfg_cb.setStyleSheet("font-size: 13px; color: #999;")
        btn_bar.addWidget(self.skip_cfg_cb)
        btn_bar.addStretch()
        self.save_btn = QPushButton("✅ 保存")
        self.save_btn.setStyleSheet("background: #ff6b81; color: white; font-size: 14px; padding: 10px 30px; border: none; border-radius: 6px;")
        self.save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(self.save_btn)
        btn_bar.addWidget(cancel_btn)
        content_layout.addLayout(btn_bar)

        main_layout.addWidget(nav_panel)
        main_layout.addWidget(content_panel, 1)
        self.setLayout(main_layout)

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

        title = QLabel("桌宠设置")
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 5px 0;")
        layout.addWidget(title)

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

        g2 = QGroupBox("参考音色参数")
        g2_layout = QFormLayout()
        g2_layout.setSpacing(14)

        self.tts_model_combo = QComboBox()
        self.tts_model_combo.addItems(["默认女声", "默认男声", "自定义"])
        g2_layout.addRow("音色模型:", self.tts_model_combo)

        speed_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(int(float(self.cfg.get("tts_speed", 1.0)) * 100))
        self.speed_label = QLabel(f"{self.cfg.get('tts_speed', 1.0):.1f}x")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"{v/100:.1f}x"))
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_label)
        g2_layout.addRow("语速:", speed_row)

        pitch_row = QHBoxLayout()
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(int(float(self.cfg.get("tts_pitch", 0.0))))
        self.pitch_label = QLabel(f"{self.cfg.get('tts_pitch', 0.0):+.1f}")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(f"{v:+d}"))
        pitch_row.addWidget(self.pitch_slider)
        pitch_row.addWidget(self.pitch_label)
        g2_layout.addRow("音调:", pitch_row)

        vol_row = QHBoxLayout()
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.cfg.get("tts_volume", 80)))
        self.vol_label = QLabel(f"{self.cfg.get('tts_volume', 80)}%")
        self.vol_slider.valueChanged.connect(lambda v: self.vol_label.setText(f"{v}%"))
        vol_row.addWidget(self.vol_slider)
        vol_row.addWidget(self.vol_label)
        g2_layout.addRow("音量:", vol_row)

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

        g1 = QGroupBox("AstrBot API 设置")
        g1_layout = QFormLayout()
        g1_layout.setSpacing(14)
        g1_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
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

        g2 = QGroupBox("TTS 模型设置")
        g2_layout = QVBoxLayout()
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

        # ── 音量调节 ──
        vol_group = QGroupBox("音量试听")
        vol_layout = QFormLayout(vol_group)
        vol_layout.setSpacing(10)
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(self.cfg.get("tts_volume", 80)))
        self.vol_value_label = QLabel(f"{self.vol_slider.value()}%")
        vol_slider_row = QHBoxLayout()
        vol_slider_row.addWidget(self.vol_slider)
        vol_slider_row.addWidget(self.vol_value_label)
        vol_layout.addRow("音量:", vol_slider_row)
        self.vol_slider.valueChanged.connect(self._on_vol_changed)
        g2_layout.addWidget(vol_group)

        self.tts_local_radio.toggled.connect(lambda: self.tts_local_widget.setVisible(self.tts_local_radio.isChecked()))
        self.tts_api_radio.toggled.connect(lambda: self.tts_api_widget.setVisible(self.tts_api_radio.isChecked()))
        self.tts_api_widget.setVisible(self.tts_api_radio.isChecked())
        self.tts_local_widget.setVisible(self.tts_local_radio.isChecked())
        g2.setLayout(g2_layout)
        layout.addWidget(g2)

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
        llm_local_path_row = QHBoxLayout()
        llm_local_path_row.addWidget(self.llm_local_model)
        llm_local_path_row.addWidget(self.llm_local_browse)
        llm_local.addRow("模型路径:", llm_local_path_row)
        self.llm_context = QSpinBox()
        self.llm_context.setRange(1024, 32768)
        self.llm_context.setValue(int(self.cfg.get("llm_context", 4096)))
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
        import urllib.request, json
        try:
            key = self.api_key.text().strip()
            url = self.api_url.text().strip()
            if not key or not url:
                QMessageBox.warning(self, "提示", "请先填写API地址和Key")
                return
            data = json.dumps({"message": "ping", "session_id": "_test"}).encode()
            req = urllib.request.Request(f"{url}/api/v1/chat", data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                QMessageBox.information(self, "连接成功", f"AstrBot API 连接成功! 状态码: {resp.status}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"无法连接 AstrBot: {str(e)[:60]}")

    def _on_vol_changed(self, val):
        self.vol_value_label.setText(f"{val}%")
        import threading, os, tempfile
        def play():
            try:
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
                from modules.voice import tts_local
                import soundfile as sf, sounddevice as sd
                tmp = os.path.join(tempfile.gettempdir(), "vol_test.wav")
                if tts_local("这个音量大小合适吗", tmp):
                    data, sr = sf.read(tmp)
                    adj = data * (val / 100.0)
                    sd.play(adj, sr)
                    sd.wait()
            except:
                pass
        threading.Thread(target=play, daemon=True).start()

    def _logout(self):
        """登出并清除会话"""
        from ui.login_ui import clear_session
        clear_session()
        self.reject()

    def _on_save(self):
        self.cfg = {
            "astrbot_api_key": self.api_key.text().strip(),
            "astrbot_url": self.api_url.text().strip(),
            "tts_speed": self.speed_slider.value() / 100,
            "tts_pitch": float(self.pitch_slider.value()),
            "tts_volume": self.vol_slider.value(),
            "tts_emotion": self.emotion_combo.currentText(),
            "tts_voice": self.tts_model_combo.currentText(),
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
            "sound_source": "",
            "window_x": -1, "window_y": -1,
        }
        # 保存到数据库
        uid = self.user.get('user_id', 0)
        if uid:
            cfg_to_db(uid, self.cfg)
        self.accepted = True
        self.accept()

    def reject(self):
        self.accepted = False
        super().reject()
