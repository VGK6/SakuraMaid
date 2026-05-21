#!/usr/bin/env python3
"""
AI 桌宠配置面板 — 基于AstrBot
"""
import sys, os, json
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_config.json")

DEFAULT_CONFIG = {
    "pet": {
        "image_path": "",
        "voice_model": "默认女声",
        "speed": 1.0,
        "pitch": 0.0,
        "volume": 80,
        "emotion": "平静"
    },
    "astrbot": {
        "enabled": True,
        "api_url": "http://localhost:6185",
        "api_key": "",
        "timeout": 30
    },
    "tts": {
        "mode": "local",
        "local_model_path": "",
        "local_device": "CPU",
        "api_provider": "OpenAI TTS",
        "api_url": "https://api.openai.com/v1/audio/speech",
        "api_key": "",
        "api_model": "tts-1"
    },
    "llm": {
        "mode": "api",
        "local_backend": "llama.cpp",
        "local_model_path": "",
        "local_context": 4096,
        "local_device": "CPU",
        "api_provider": "OpenAI",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "api_key": "",
        "api_model": "deepseek-v4-flash"
    }
}

# ── 左侧导航按钮 ──
class NavButton(QPushButton):
    clicked_page = Signal(int)

    def __init__(self, icon_text, text, page_idx):
        super().__init__()
        self.setCheckable(True)
        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)
        self._page = page_idx
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.addWidget(QLabel(icon_text))
        layout.addWidget(QLabel(text))
        layout.addStretch()
        self.clicked.connect(lambda: self.clicked_page.emit(page_idx))
        self.setStyleSheet("""
            QPushButton { text-align:left; border:none; border-radius:8px; padding:8px; font:13px; }
            QPushButton:hover { background:#f0f0f0; }
            QPushButton:checked { background:#ff6b81; color:white; }
        """)

# ── 图片预览区域 ──
class ImagePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(140, 140)
        self.setStyleSheet("background:#f5f5f5; border:2px dashed #ddd; border-radius:12px;")
        self._pixmap = None

    def set_image(self, path):
        if path and os.path.exists(path):
            self._pixmap = QPixmap(path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self._pixmap = None
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self._pixmap:
            px = (140 - self._pixmap.width()) // 2
            py = (140 - self._pixmap.height()) // 2
            p.drawPixmap(px, py, self._pixmap)
        else:
            p.setPen(QColor(180, 180, 180))
            p.setFont(QFont('Microsoft YaHei', 10))
            p.drawText(self.rect(), Qt.AlignCenter, "📷\n暂无图片")

# ── 桌宠设置页 ──
class PetSettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 参考图
        grp1 = QGroupBox("桌宠参考图")
        g1 = QHBoxLayout(grp1)
        self.preview = ImagePreview()
        g1.addWidget(self.preview)
        v1 = QVBoxLayout()
        self.btn_upload = QPushButton("📁 上传图片")
        self.btn_reset = QPushButton("↺ 重置默认")
        v1.addWidget(self.btn_upload)
        v1.addWidget(self.btn_reset)
        v1.addWidget(QLabel("支持格式: PNG, JPG, GIF\n建议尺寸: 256×256"))
        v1.addStretch()
        g1.addLayout(v1)
        layout.addWidget(grp1)

        # 音色参数
        grp2 = QGroupBox("参考音色参数")
        g2 = QFormLayout(grp2)
        g2.setSpacing(10)

        self.combo_voice = QComboBox()
        self.combo_voice.addItems(["默认女声", "温柔女声", "可爱少女", "沉稳男声", "清澈童声"])
        g2.addRow("音色模型:", self.combo_voice)

        self.slider_speed = self._make_slider(0.5, 2.0, 1.0, "x")
        g2.addRow("语速:", self.slider_speed)

        self.slider_pitch = self._make_slider(-5, 5, 0, "")
        g2.addRow("音调:", self.slider_pitch)

        self.slider_volume = self._make_slider(0, 100, 80, "%")
        g2.addRow("音量:", self.slider_volume)

        self.combo_emotion = QComboBox()
        self.combo_emotion.addItems(["平静", "开心", "悲伤", "鼓励", "疑惑"])
        g2.addRow("情感:", self.combo_emotion)

        btn_row = QHBoxLayout()
        self.btn_preview = QPushButton("▶ 试听示例")
        self.btn_save_preset = QPushButton("💾 保存为预设")
        btn_row.addWidget(self.btn_preview)
        btn_row.addWidget(self.btn_save_preset)
        btn_row.addStretch()
        g2.addRow("", btn_row)

        layout.addWidget(grp2)
        layout.addStretch()

    def _make_slider(self, min_v, max_v, default, suffix):
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        s = QSlider(Qt.Horizontal)
        s.setRange(int(min_v * 100), int(max_v * 100))
        s.setValue(int(default * 100))
        label = QLabel(f"{default}{suffix}")
        s.valueChanged.connect(lambda v: label.setText(f"{v/100:.1f}{suffix}" if suffix == "x" else f"{v}{suffix}"))
        hl.addWidget(s)
        hl.addWidget(label)
        return w

# ── 系统配置页 ──
class SystemConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # AstrBot API
        grp_a = QGroupBox("AstrBot API 设置")
        ga = QFormLayout(grp_a)
        self.chk_api = QCheckBox("开启")
        self.chk_api.setChecked(True)
        ga.addRow("启用 API:", self.chk_api)
        self.edit_api_url = QLineEdit("http://localhost:6185")
        ga.addRow("API 地址:", self.edit_api_url)
        self.edit_api_key = QLineEdit()
        self.edit_api_key.setEchoMode(QLineEdit.Password)
        self.btn_show_key = QPushButton("显示")
        self.btn_show_key.setCheckable(True)
        hk = QHBoxLayout()
        hk.addWidget(self.edit_api_key)
        hk.addWidget(self.btn_show_key)
        ga.addRow("API Key:", hk)
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(5, 120)
        self.spin_timeout.setValue(30)
        ga.addRow("超时时间:", self.spin_timeout)
        self.btn_test = QPushButton("🔌 测试连接")
        ga.addRow("", self.btn_test)
        layout.addWidget(grp_a)

        # TTS
        grp_t = QGroupBox("TTS 模型设置")
        gt = QFormLayout(grp_t)
        self.tts_mode = QComboBox()
        self.tts_mode.addItems(["本地", "API"])
        gt.addRow("模式:", self.tts_mode)

        self.stacked_tts = QStackedWidget()
        # 本地TTS
        w_local = QWidget()
        fl = QFormLayout(w_local)
        self.edit_tts_path = QLineEdit()
        self.btn_tts_browse = QPushButton("浏览")
        hp = QHBoxLayout(); hp.addWidget(self.edit_tts_path); hp.addWidget(self.btn_tts_browse)
        fl.addRow("模型路径:", hp)
        self.combo_tts_dev = QComboBox(); self.combo_tts_dev.addItems(["CPU", "CUDA"])
        fl.addRow("设备:", self.combo_tts_dev)
        self.stacked_tts.addWidget(w_local)

        # API TTS
        w_api = QWidget()
        fa = QFormLayout(w_api)
        self.combo_tts_provider = QComboBox()
        self.combo_tts_provider.addItems(["OpenAI TTS", "Azure TTS", "ElevenLabs"])
        fa.addRow("Provider:", self.combo_tts_provider)
        self.edit_tts_api_url = QLineEdit("https://api.openai.com/v1/audio/speech")
        fa.addRow("API URL:", self.edit_tts_api_url)
        self.edit_tts_api_key = QLineEdit(); self.edit_tts_api_key.setEchoMode(QLineEdit.Password)
        fa.addRow("API Key:", self.edit_tts_api_key)
        self.edit_tts_model = QLineEdit("tts-1")
        fa.addRow("模型名:", self.edit_tts_model)
        self.stacked_tts.addWidget(w_api)

        self.tts_mode.currentIndexChanged.connect(self.stacked_tts.setCurrentIndex)
        gt.addRow("", self.stacked_tts)
        layout.addWidget(grp_t)

        # LLM
        grp_l = QGroupBox("LLM 模型设置")
        gl = QFormLayout(grp_l)
        self.llm_mode = QComboBox()
        self.llm_mode.addItems(["本地", "API"])
        gl.addRow("模式:", self.llm_mode)

        self.stacked_llm = QStackedWidget()
        wl_local = QWidget()
        fll = QFormLayout(wl_local)
        self.combo_llm_backend = QComboBox()
        self.combo_llm_backend.addItems(["llama.cpp", "Ollama", "vLLM"])
        fll.addRow("后端框架:", self.combo_llm_backend)
        self.edit_llm_path = QLineEdit()
        self.btn_llm_browse = QPushButton("浏览")
        hp2 = QHBoxLayout(); hp2.addWidget(self.edit_llm_path); hp2.addWidget(self.btn_llm_browse)
        fll.addRow("模型路径:", hp2)
        self.spin_llm_ctx = QSpinBox(); self.spin_llm_ctx.setRange(1024, 32768); self.spin_llm_ctx.setValue(4096)
        fll.addRow("上下文长度:", self.spin_llm_ctx)
        self.combo_llm_dev = QComboBox(); self.combo_llm_dev.addItems(["CPU", "CUDA"])
        fll.addRow("推理设备:", self.combo_llm_dev)
        self.stacked_llm.addWidget(wl_local)

        wl_api = QWidget()
        fla = QFormLayout(wl_api)
        self.combo_llm_provider = QComboBox()
        self.combo_llm_provider.addItems(["OpenAI", "Anthropic", "自定义"])
        fla.addRow("Provider:", self.combo_llm_provider)
        self.edit_llm_api_url = QLineEdit("https://api.deepseek.com/v1/chat/completions")
        fla.addRow("API URL:", self.edit_llm_api_url)
        self.edit_llm_api_key = QLineEdit(); self.edit_llm_api_key.setEchoMode(QLineEdit.Password)
        fla.addRow("API Key:", self.edit_llm_api_key)
        self.edit_llm_model = QLineEdit("deepseek-v4-flash")
        fla.addRow("模型名:", self.edit_llm_model)
        self.stacked_llm.addWidget(wl_api)

        self.llm_mode.currentIndexChanged.connect(self.stacked_llm.setCurrentIndex)
        gl.addRow("", self.stacked_llm)
        layout.addWidget(grp_l)
        layout.addStretch()

# ── 主窗口 ──
class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 桌宠配置面板")
        self.resize(820, 650)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        hl = QHBoxLayout(central)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        # 左侧导航
        nav = QWidget()
        nav.setFixedWidth(160)
        nav.setStyleSheet("background:#fafafa; border-right:1px solid #eee;")
        vl = QVBoxLayout(nav)
        vl.setContentsMargins(8, 16, 8, 16)
        vl.setSpacing(4)

        title = QLabel("🌸 樱花庄")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font:bold 16px; color:#ff6b81; padding:8px;")
        vl.addWidget(title)

        self.nav_pet = NavButton("🖼️", "桌宠设置", 0)
        self.nav_sys = NavButton("⚙️", "系统配置", 1)
        self.nav_pet.setChecked(True)
        vl.addWidget(self.nav_pet)
        vl.addWidget(self.nav_sys)
        vl.addStretch()

        self.nav_pet.clicked_page.connect(self._switch_page)
        self.nav_sys.clicked_page.connect(self._switch_page)

        hl.addWidget(nav)

        # 右侧内容
        self.stack = QStackedWidget()
        self.pet_page = PetSettingsPage()
        self.sys_page = SystemConfigPage()
        self.stack.addWidget(self.pet_page)
        self.stack.addWidget(self.sys_page)
        hl.addWidget(self.stack, 1)

        # 底部按钮
        bottom = QWidget()
        bh = QHBoxLayout(bottom)
        bh.addStretch()
        btn_save = QPushButton("💾 保存")
        btn_save.setStyleSheet("background:#ff6b81; color:white; padding:8px 24px; border-radius:6px; font:13px;")
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet("padding:8px 24px; border-radius:6px; font:13px;")
        bh.addWidget(btn_save)
        bh.addWidget(btn_cancel)
        self.stack.addWidget(bottom)
        self.statusBar().addPermanentWidget(bottom)

    def _switch_page(self, idx):
        self.nav_pet.setChecked(idx == 0)
        self.nav_sys.setChecked(idx == 1)
        self.stack.setCurrentIndex(idx)

    def _load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        p = cfg.get("pet", {})
        self.pet_page.combo_voice.setCurrentText(p.get("voice_model", "默认女声"))
        self.pet_page.combo_emotion.setCurrentText(p.get("emotion", "平静"))
        if p.get("image_path"):
            self.pet_page.preview.set_image(p["image_path"])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = ConfigWindow()
    win.show()
    sys.exit(app.exec())
