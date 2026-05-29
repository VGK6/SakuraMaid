"""
配置UI — 左侧导航 + 右侧内容面板
所有配置读写走数据库
修复: 最大化/最小化按钮、输入框重叠、按键逻辑、音量试听
"""
import os, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from modules.database import get_settings, save_setting

# 启动时预生成音量试听音频（只生成一次，后续直接用）
import os as _vol_os, subprocess as _vol_sp, sys as _vol_sys
_vol_path = _vol_os.path.join(_vol_os.path.dirname(_vol_os.path.dirname(_vol_os.path.dirname(_vol_os.path.abspath(__file__)))),
                              "resourses", "temp", "vol_test.wav")
_vol_os.makedirs(_vol_os.path.dirname(_vol_path), exist_ok=True)
if not _vol_os.path.exists(_vol_path):
    try:
        _vol_sp.run([_vol_sys.executable, '-u', '-c',
            f"import asyncio, edge_tts; "
            f"asyncio.run(edge_tts.Communicate('这个音量大小合适吗','zh-CN-XiaoxiaoNeural').save(r'{_vol_path}'))"],
            capture_output=True, timeout=60)
    except:
        pass

from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
                               QLineEdit, QComboBox, QPushButton, QSlider, QCheckBox,
                               QGroupBox, QFormLayout, QFileDialog, QFrame,
                               QSpinBox, QRadioButton, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap


def db_to_cfg(user_id: int) -> dict:
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
        "voice_lang": g("voice.lang", "auto"),
        "bubble_lang": g("bubble.lang", "auto"),
        "tts_voice": g("tts.voice", "默认女声"),
        "tts_mode": g("tts.mode", "api"),
        "llm_mode": g("llm.mode", "api"),
        "character_name": g("pet.character", "小女仆"),
        "sound_source": g("pet.sound_source", ""),
        "personality": g("pet.personality", "温柔贴心"),
        "personality_prompt": g("pet.personality_prompt", ""),
        "user_title": g("pet.user_title", "龙之介大人"),
        "talk_style": g("pet.talk_style", "正常"),
        "window_x": int(g("window_x", "-1")),
        "window_y": int(g("window_y", "-1")),
    }
    return out


def cfg_to_db(user_id: int, cfg: dict):
    mapping = [
        ("astrbot", "url", cfg.get("astrbot_url", "")),
        ("astrbot", "api_key", cfg.get("astrbot_api_key", "")),
        ("tts", "speed", str(cfg.get("tts_speed", 1.0))),
        ("tts", "pitch", str(cfg.get("tts_pitch", 0.0))),
        ("tts", "volume", str(cfg.get("tts_volume", 80))),
        ("tts", "emotion", cfg.get("tts_emotion", "平静")),
        ("tts", "voice", cfg.get("tts_voice", "默认女声")),
        ("tts", "mode", cfg.get("tts_mode", "api")),
        ("voice", "lang", cfg.get("voice_lang", "auto")),
        ("bubble", "lang", cfg.get("bubble_lang", "auto")),
        ("pet", "character", cfg.get("character_name", "小女仆")),
        ("pet", "sound_source", cfg.get("sound_source", "")),
        ("pet", "personality", cfg.get("personality", "温柔贴心")),
        ("pet", "personality_prompt", cfg.get("personality_prompt", "")),
        ("pet", "user_title", cfg.get("user_title", "龙之介大人")),
        ("pet", "talk_style", cfg.get("talk_style", "正常")),
    ]
    for cat, key, val in mapping:
        save_setting(user_id, cat, key, str(val))


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
        self.resize(960, 720)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setStyleSheet("""
            QWidget { font-family: Microsoft YaHei; font-size: 14px; background: #fafafa; }
            QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 8px; 
                       margin-top: 10px; padding: 18px; background: white; }
            QGroupBox::title { color: #ff6b81; subcontrol-origin: margin; left: 12px; font-size: 14px; }
            QLineEdit, QComboBox { padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; 
                                  background: white; font-size: 13px; min-height: 26px; }
            QPushButton { padding: 8px 16px; border-radius: 6px; font-size: 13px; 
                         background: #f0f0f0; border: 1px solid #ddd; min-height: 26px; }
            QPushButton:hover { background: #ff6b81; color: white; border-color: #ff6b81; }
            QSlider::groove:horizontal { height: 6px; background: #ddd; border-radius: 3px; }
            QSlider::handle:horizontal { background: #ff6b81; width: 18px; height: 18px; 
                                        margin: -6px 0; border-radius: 9px; }
            QRadioButton { spacing: 8px; font-size: 14px; }
            QRadioButton::indicator { width: 18px; height: 18px; border-radius: 3px; border: 2px solid #ccc; background: white; }
            QRadioButton::indicator:checked { background: #4CAF50; border-color: #4CAF50; }
            QCheckBox { spacing: 8px; font-size: 14px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 3px; border: 2px solid #ccc; background: white; }
            QCheckBox::indicator:checked { background: #4CAF50; border-color: #4CAF50; }
            QSpinBox { padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; min-height: 28px; }
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
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 10px 0 5px 0;")
        nav_layout.addWidget(title)

        if self.user:
            user_btn = QPushButton(f"👤 {self.user.get('nickname', self.user.get('username',''))}  ▼")
            user_btn.setStyleSheet("text-align: center; padding: 8px; border: none; color: #999; font-size: 12px; background: transparent;")
            user_btn.clicked.connect(self._logout)
            nav_layout.addWidget(user_btn)

        self.nav_btns = []
        nav_items = [("🖼️", "桌宠设置", 0), ("⚙️", "系统配置", 1), ("🧠", "技能管理", 2), ("🎭", "人格记忆", 3)]
        self.stacked = QStackedWidget()

        for icon, text, idx in nav_items:
            btn = NavButton(icon, text, idx)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self.nav_btns.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        ver = QLabel("v1测试版")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #ccc; font-size: 11px; padding: 10px;")
        nav_layout.addWidget(ver)

        # ====== 右侧内容 ======
        content_panel = QFrame()
        content_panel.setStyleSheet("background: #fafafa;")
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(25, 20, 25, 20)

        page0 = self._build_pet_page()
        self.stacked.addWidget(page0)
        page1 = self._build_system_page()
        self.stacked.addWidget(page1)
        page2 = self._build_skill_page()
        self.stacked.addWidget(page2)
        page3 = self._build_personality_page()
        self.stacked.addWidget(page3)

        content_layout.addWidget(self.stacked)

        # 跳过配置 + 按钮
        btn_bar = QHBoxLayout()
        self.skip_cfg_cb = QCheckBox("跳过配置，直接启动")
        self.skip_cfg_cb.setStyleSheet("font-size: 13px; color: #999;")
        btn_bar.addWidget(self.skip_cfg_cb)
        btn_bar.addStretch()
        self.save_btn = QPushButton("✅ 保存并应用")
        self.save_btn.setStyleSheet("background: #ff6b81; color: white; font-size: 15px; padding: 12px 35px; border: none; border-radius: 8px; font-weight: bold;")
        self.save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("font-size: 14px; padding: 12px 25px;")
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
        title.setFont(QFont('Microsoft YaHei', 17, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 8px 0;")
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
        fmt_label.setStyleSheet("color: #999; font-size: 12px;")
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
        g2_layout.setSpacing(15)
        g2_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

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

        # 音量（预加载音频 + 线程循环播放）
        import threading, time
        vol_row = QHBoxLayout()
        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setRange(0, 100)
        vol_slider.setValue(int(self.cfg.get("tts_volume", 80)))
        vol_label = QLabel(f"{vol_slider.value()}%")
        vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))

        # 预加载音频
        self._vol_audio_data = None
        self._vol_sample_rate = None
        if _vol_os.path.exists(_vol_path):
            try:
                import soundfile as sf
                self._vol_audio_data, self._vol_sample_rate = sf.read(_vol_path)
            except Exception as e:
                print(f"加载音量提示音失败: {e}")
        else:
            print(f"音量提示音文件不存在: {_vol_path}")

        # 线程控制变量
        self._vol_playing = False
        self._vol_stop_event = None

        def _vol_play_loop():
            """循环播放，每次播放前根据滑块当前值调整音量"""
            import sounddevice as sd
            stop_event = self._vol_stop_event
            data = self._vol_audio_data
            sr = self._vol_sample_rate
            if data is None:
                return
            while not stop_event.is_set():
                val = vol_slider.value()
                gain = val / 100.0
                adjusted = data * gain
                sd.play(adjusted, sr)
                duration = len(adjusted) / sr
                elapsed = 0
                while elapsed < duration and not stop_event.is_set():
                    time.sleep(0.05)
                    elapsed += 0.05
                sd.stop()  # 安全停止
                if stop_event.is_set():
                    break

        def _start_vol_loop():
            if self._vol_playing or self._vol_audio_data is None:
                return
            self._vol_playing = True
            self._vol_stop_event = threading.Event()
            self._vol_thread = threading.Thread(target=_vol_play_loop, daemon=True)
            self._vol_thread.start()

        def _stop_vol_loop():
            """停止循环：让当前音频播完，不再继续"""
            if not self._vol_playing:
                return
            self._vol_stop_event.set()
            # 等待线程退出（播放完当前遍自然结束）
            if self._vol_thread and self._vol_thread.is_alive():
                self._vol_thread.join(timeout=2.0)
            self._vol_playing = False
            self._vol_thread = None
            self._vol_stop_event = None

        vol_slider.sliderPressed.connect(_start_vol_loop)
        vol_slider.sliderReleased.connect(_stop_vol_loop)
        vol_row.addWidget(vol_slider)
        vol_row.addWidget(vol_label)
        g2_layout.addRow("音量:", vol_row)
        self._pet_vol_slider = vol_slider

        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["平静", "开心", "悲伤", "鼓励"])
        self.emotion_combo.setCurrentText(self.cfg.get("tts_emotion", "平静"))
        g2_layout.addRow("情感:", self.emotion_combo)

        # 语音语种
        lang_map = {"自动检测": "auto", "中文": "zh", "日文": "ja", "英文": "en"}
        self.voice_lang_combo = QComboBox()
        self.voice_lang_combo.addItems(["自动检测", "中文", "日文", "英文"])
        current_vlang = self.cfg.get("voice_lang", "auto")
        for i in range(self.voice_lang_combo.count()):
            if lang_map[self.voice_lang_combo.itemText(i)] == current_vlang:
                self.voice_lang_combo.setCurrentIndex(i)
                break
        g2_layout.addRow("语音语种:", self.voice_lang_combo)

        # 气泡语种
        self.bubble_lang_combo = QComboBox()
        self.bubble_lang_combo.addItems(["自动检测", "中文", "日文", "英文"])
        current_blang = self.cfg.get("bubble_lang", "auto")
        for i in range(self.bubble_lang_combo.count()):
            if lang_map[self.bubble_lang_combo.itemText(i)] == current_blang:
                self.bubble_lang_combo.setCurrentIndex(i)
                break
        g2_layout.addRow("气泡语种:", self.bubble_lang_combo)

        btn_row = QHBoxLayout()
        self.test_btn = QPushButton("🎧 试听示例")
        self.test_btn.clicked.connect(self._play_test_voice)
        self.save_preset_btn = QPushButton("💾 保存为预设")
        self.save_preset_btn.clicked.connect(self._save_preset)
        btn_row.addWidget(self.test_btn)
        btn_row.addWidget(self.save_preset_btn)
        btn_row.addStretch()
        g2_layout.addRow("", btn_row)
        g2.setLayout(g2_layout)
        layout.addWidget(g2)

        # ── 音色克隆 ──
        g3 = QGroupBox("音色克隆")
        g3_layout = QFormLayout()
        g3_layout.setSpacing(12)
        self.clone_path_edit = QLineEdit(self.cfg.get("sound_source", ""))
        self.clone_path_edit.setPlaceholderText("选择参考音频文件 (.wav)")
        self.clone_browse_btn = QPushButton("浏览...")
        self.clone_browse_btn.clicked.connect(lambda: self._browse_audio())
        clone_row = QHBoxLayout()
        clone_row.addWidget(self.clone_path_edit)
        clone_row.addWidget(self.clone_browse_btn)
        g3_layout.addRow("参考音频:", clone_row)
        clone_info = QLabel("提示：选择一段目标人声的wav音频(建议5-30秒)，保存后语音播报将使用此音色克隆")
        clone_info.setStyleSheet("color: #999; font-size: 11px;")
        g3_layout.addRow("", clone_info)

        # 音色管理
        vm_label = QLabel("已克隆的音色:")
        vm_label.setStyleSheet("color: #ff6b81; font-weight: bold; font-size: 12px;")
        g3_layout.addRow("", vm_label)
        self.vm_voice_combo = QComboBox()
        vm_row = QHBoxLayout()
        vm_row.addWidget(self.vm_voice_combo)
        self.vm_refresh_btn = QPushButton("刷新")
        self.vm_refresh_btn.clicked.connect(self._refresh_voices)
        self.vm_use_btn = QPushButton("设为当前")
        self.vm_use_btn.clicked.connect(self._use_voice)
        self.vm_del_btn = QPushButton("删除")
        self.vm_del_btn.setStyleSheet("color: #f44336;")
        self.vm_del_btn.clicked.connect(self._delete_voice)
        vm_row.addWidget(self.vm_refresh_btn)
        vm_row.addWidget(self.vm_use_btn)
        vm_row.addWidget(self.vm_del_btn)
        g3_layout.addRow("", vm_row)

        g3.setLayout(g3_layout)
        layout.addWidget(g3)

        layout.addStretch()
        return page

    # ── 音量实时试听 ──
    def _play_vol_test(self, vol: int):
        """用预加载的本地音频实时调音量"""
        if hasattr(self, '_vol_audio'):
            import sounddevice as sd
            adj = self._vol_audio * (vol / 100.0)
            sd.play(adj, self._vol_sr)

    def _play_test_voice(self):
        """试听示例（子进程播放）"""
        import threading, subprocess, sys, os, tempfile
        tmp_dir = tempfile.gettempdir()
        def play():
            subprocess.run(
                [sys.executable, '-u', '-c',
                 f"import asyncio, edge_tts, soundfile as sf, sounddevice as sd; "
                 f"asyncio.run(edge_tts.Communicate('你好，欢迎使用樱花桌宠软件！','zh-CN-XiaoxiaoNeural').save(r'{tmp_dir}/test_voice.wav')); "
                 f"d,sr=sf.read(r'{tmp_dir}/test_voice.wav'); sd.play(d, sr); sd.wait()"],
                capture_output=True, timeout=60
            )
        threading.Thread(target=play, daemon=True).start()

    def _save_preset(self):
        """保存音色预设"""
        from PySide6.QtWidgets import QMessageBox
        import json
        from modules.database import save_setting
        preset = {
            "speed": self.speed_slider.value() / 100,
            "pitch": float(self.pitch_slider.value()),
            "volume": self._pet_vol_slider.value(),
            "emotion": self.emotion_combo.currentText(),
            "voice": self.tts_model_combo.currentText(),
        }
        uid = self.user.get('user_id', 0)
        if uid:
            save_setting(uid, "preset", "voice_params", json.dumps(preset))
            QMessageBox.information(self, "✅", "音色预设已保存!")
        else:
            QMessageBox.warning(self, "⚠️", "请先登录")

    # ── 页面2: 系统配置 ──
    def _build_system_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("系统配置")
        title.setFont(QFont('Microsoft YaHei', 17, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 8px 0;")
        layout.addWidget(title)

        g1 = QGroupBox("AstrBot API 设置")
        g1_layout = QFormLayout()
        g1_layout.setSpacing(12)
        self.api_enable = QCheckBox("启用 API")
        self.api_enable.setChecked(True)
        self.api_url = QLineEdit(self.cfg.get("astrbot_url", "http://127.0.0.1:6185"))
        self.api_key = QLineEdit(self.cfg.get("astrbot_api_key", ""))
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_show_btn = QPushButton("显示")
        self.api_show_btn.setFixedWidth(60)
        self.api_show_btn.clicked.connect(lambda: self.api_key.setEchoMode(QLineEdit.Normal if self.api_key.echoMode() else QLineEdit.Password))
        api_key_row = QHBoxLayout()
        api_key_row.addWidget(self.api_key)
        api_key_row.addWidget(self.api_show_btn)
        self.test_api_btn = QPushButton("🔗 测试连接")
        self.test_api_btn.clicked.connect(self._test_api)
        g1_layout.addRow("", self.api_enable)
        g1_layout.addRow("API 地址:", self.api_url)
        g1_layout.addRow("API Key:", api_key_row)
        g1_layout.addRow("", self.test_api_btn)
        g1.setLayout(g1_layout)
        layout.addWidget(g1)

        # ── TTS 模型设置 ──
        g2 = QGroupBox("TTS 模型设置")
        g2_layout = QVBoxLayout()
        mode_row = QHBoxLayout()
        self.tts_local_radio = QRadioButton("本地")
        self.tts_api_radio = QRadioButton("API")
        self.tts_api_radio.setChecked(True)
        mode_row.addWidget(QLabel("模式:"))
        mode_row.addWidget(self.tts_local_radio)
        mode_row.addWidget(self.tts_api_radio)
        mode_row.addStretch()
        g2_layout.addLayout(mode_row)

        self.tts_local_widget = QWidget()
        tts_local = QFormLayout(self.tts_local_widget)
        self.tts_local_path = QLineEdit(self.cfg.get("tts_local_model_path", ""))
        self.tts_local_browse = QPushButton("浏览...")
        self.tts_local_browse.clicked.connect(lambda: self._browse_file(self.tts_local_path, "模型文件 (*.onnx *.pt)"))
        tts_local_path_row = QHBoxLayout()
        tts_local_path_row.addWidget(self.tts_local_path)
        tts_local_path_row.addWidget(self.tts_local_browse)
        tts_local.addRow("模型路径:", tts_local_path_row)
        self.tts_local_device = QComboBox()
        self.tts_local_device.addItems(["CPU", "CUDA"])
        tts_local.addRow("设备:", self.tts_local_device)
        g2_layout.addWidget(self.tts_local_widget)

        self.tts_api_widget = QWidget()
        tts_api = QFormLayout(self.tts_api_widget)
        tts_api.setSpacing(12)
        self.tts_api_provider = QComboBox()
        self.tts_api_provider.addItems(["其他供应商", "Edge TTS"])
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

        # ── LLM 模型设置 ──
        g3 = QGroupBox("LLM 模型设置")
        g3_layout = QVBoxLayout()
        llm_mode_row = QHBoxLayout()
        self.llm_local_radio = QRadioButton("本地")
        self.llm_api_radio = QRadioButton("API")
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
        self.llm_local_browse = QPushButton("浏览...")
        self.llm_local_browse.clicked.connect(lambda: self._browse_file(self.llm_local_model, "模型文件 (*.gguf *.bin)"))
        llm_local_path_row = QHBoxLayout()
        llm_local_path_row.addWidget(self.llm_local_model)
        llm_local_path_row.addWidget(self.llm_local_browse)
        llm_local.addRow("模型路径:", llm_local_path_row)
        self.llm_context = QSpinBox()
        self.llm_context.setRange(1024, 32768)
        self.llm_context.setValue(int(self.cfg.get("llm_context", 4096)))
        self.llm_context.setSingleStep(1024)
        self.llm_context.setFixedWidth(160)
        self.llm_context.setStyleSheet("""
            QSpinBox { padding: 4px 8px; font-size: 13px; min-height: 22px; }
            QSpinBox::up-button { width: 24px; height: 18px; }
            QSpinBox::down-button { width: 24px; height: 18px; }
        """)
        llm_local.addRow("上下文长度:", self.llm_context)
        self.llm_device = QComboBox()
        self.llm_device.addItems(["CPU", "CUDA"])
        llm_local.addRow("推理设备:", self.llm_device)
        g3_layout.addWidget(self.llm_local_widget)

        self.llm_api_widget = QWidget()
        llm_api = QFormLayout(self.llm_api_widget)
        llm_api.setSpacing(12)
        self.llm_api_provider = QComboBox()
        self.llm_api_provider.addItems(["其他供应商", "DeepSeek", "Ollama"])
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

    def _build_personality_page(self):
        """人格记忆设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        title = QLabel("🎭 人格与记忆")
        title.setFont(QFont('Microsoft YaHei', 17, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 8px 0;")
        layout.addWidget(title)

        g1 = QGroupBox("桌宠人格设置")
        g1_layout = QFormLayout()
        g1_layout.setSpacing(12)

        self.personality_combo = QComboBox()
        self.personality_combo.addItems(["温柔贴心", "活泼可爱", "傲娇毒舌", "冷静理智", "治愈系"])
        self.personality_combo.setCurrentText(self.cfg.get("personality", "温柔贴心"))
        g1_layout.addRow("人格类型:", self.personality_combo)

        self.talk_style_combo = QComboBox()
        self.talk_style_combo.addItems(["正常", "简短", "详细", "带表情"])
        self.talk_style_combo.setCurrentText(self.cfg.get("talk_style", "正常"))
        g1_layout.addRow("说话风格:", self.talk_style_combo)

        self.user_title = QLineEdit(self.cfg.get("user_title", "龙之介大人"))
        self.user_title.setPlaceholderText("桌宠对您的称呼，如：主人、哥哥、先生")
        g1_layout.addRow("对用户称谓:", self.user_title)

        self.personality_prompt = QLineEdit(self.cfg.get("personality_prompt", ""))
        self.personality_prompt.setPlaceholderText("人格提示词，如：你是一个温柔贴心的女仆，总是关心主人")
        g1_layout.addRow("人格提示词:", self.personality_prompt)

        g1.setLayout(g1_layout)
        layout.addWidget(g1)

        # 从AstrBot导入
        import_btn = QPushButton("🔄 从AstrBot智能体导入人格")
        import_btn.setStyleSheet("background: #ff6b81; color: white; padding: 12px; font-size: 14px; border-radius: 8px;")
        import_btn.clicked.connect(self._import_from_astrbot)
        layout.addWidget(import_btn)

        # AstrBot记忆系统
        g2 = QGroupBox("记忆系统")
        g2_layout = QVBoxLayout()
        mem_info = QLabel("桌宠记忆功能通过 AstrBot 的本地回忆插件提供。对话历史、用户偏好、重要事件等信息会被自动记录。")
        mem_info.setWordWrap(True)
        mem_info.setStyleSheet("color: #666; font-size: 13px; padding: 10px;")
        g2_layout.addWidget(mem_info)
        g2.setLayout(g2_layout)
        layout.addWidget(g2)

        layout.addStretch()
        return page

    def _import_from_astrbot(self):
        """从AstrBot导入智能体人格设置"""
        from PySide6.QtWidgets import QMessageBox
        from modules.astrbot_client import chat
        try:
            reply = chat("请介绍你自己，包括你的人格设定、性格特点和说话风格，简要回答即可。", session_id="_get_personality")
            if reply:
                self.personality_prompt.setText(reply[:200])
                QMessageBox.information(self, "导入成功", "已从AstrBot获取智能体信息并填入人格提示词")
            else:
                QMessageBox.warning(self, "导入失败", "无法获取AstrBot智能体信息")
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"连接AstrBot失败: {str(e)[:60]}")

    def _browse_file(self, line_edit: QLineEdit, file_filter: str):
        """打开文件选择器"""
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", file_filter)
        if path:
            line_edit.setText(path)

    def _browse_audio(self):
        """选择音色克隆音频"""
        path, _ = QFileDialog.getOpenFileName(self, "选择参考音频", "",
                                               "音频文件 (*.wav *.mp3 *.ogg)")
        if path:
            self.clone_path_edit.setText(path)

    def _refresh_voices(self):
        """刷新音色列表"""
        import urllib.request, json
        key = __import__('os').environ.get("MINIMAX_API_KEY", "")
        if not key:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "未配置MiniMax API Key")
            return
        try:
            # 从数据库读已保存的音色
            from modules.database import get_conn
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE category='minimax' AND key='voice_map'")
            voices = {"female-shaonv": "默认女声"}
            for row in c.fetchall():
                vm = json.loads(row['value'])
                vid = vm.get("voice_id", "")
                if vid:
                    voices[vid] = vm.get("path", "克隆音色")
            conn.close()
            self.vm_voice_combo.clear()
            for vid, name in voices.items():
                self.vm_voice_combo.addItem(f"{os.path.basename(name)} ({vid[:12]}...)", vid)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "刷新完成", f"找到 {len(voices)} 个音色")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "刷新失败", str(e)[:50])

    def _use_voice(self):
        """设为当前音色"""
        vid = self.vm_voice_combo.currentData()
        if vid:
            __import__('os').environ["MINIMAX_VOICE_ID"] = vid
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "设置成功", f"已切换音色: {self.vm_voice_combo.currentText()}")

    def _delete_voice(self):
        """删除音色"""
        vid = self.vm_voice_combo.currentData()
        if not vid or vid in ("female-shaonv",):
            return
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "确认删除", f"确定要删除音色 {self.vm_voice_combo.currentText()} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import urllib.request, json
                key = __import__('os').environ.get("MINIMAX_API_KEY", "")
                data = json.dumps({"voice_id": vid}).encode()
                req = urllib.request.Request("https://api.minimax.chat/v1/voice_clone", data=data,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    method="DELETE")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    QMessageBox.information(self, "删除成功", f"音色 {vid} 已删除")
                    self._refresh_voices()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", str(e)[:50])

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
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if "未授权" in body or "401" in str(e):
                QMessageBox.warning(self, "连接失败", f"API Key无效或未授权，请在AstrBot后台添加此Key")
            else:
                QMessageBox.warning(self, "连接失败", f"HTTP {e.code}: {body[:50]}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"无法连接: {str(e)[:60]}")

    def _build_skill_page(self):
        """技能管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("🧠 技能管理")
        title.setFont(QFont('Microsoft YaHei', 17, QFont.Bold))
        title.setStyleSheet("color: #ff6b81; padding: 0 0 8px 0;")
        layout.addWidget(title)

        desc = QLabel("管理桌宠已学会的自定义技能")
        desc.setStyleSheet("color: #999; font-size: 13px; padding-bottom: 10px;")
        layout.addWidget(desc)

        from modules.self_evolution.skill_registry import SkillRegistry
        reg = SkillRegistry()
        skills = reg.list_all(enabled_only=False)

        if not skills:
            no_skill = QLabel("📭 暂无已注册的技能")
            no_skill.setAlignment(Qt.AlignCenter)
            no_skill.setStyleSheet("color: #bbb; font-size: 14px; padding: 40px;")
            layout.addWidget(no_skill)
        else:
            for s in skills:
                skill_box = QFrame()
                skill_box.setStyleSheet("QFrame { background: white; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin: 5px; }")
                box_layout = QVBoxLayout(skill_box)
                box_layout.setContentsMargins(5, 5, 5, 5)

                name_row = QHBoxLayout()
                name_label = QLabel(f"{'🟢' if s['enabled'] else '🔴'} {s['name']}")
                name_label.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
                name_label.setStyleSheet("color: #333;")
                name_row.addWidget(name_label)

                score = s['health_score']
                score_label = QLabel(f"评分: {score:.0f}" if score else "新技能")
                score_label.setStyleSheet(f"color: {'#4CAF50' if score > 60 else '#FF9800' if score > 30 else '#f44336'}; font-size: 12px;")
                name_row.addWidget(score_label)
                name_row.addStretch()

                ver_label = QLabel(f"v{s['version']}")
                ver_label.setStyleSheet("color: #bbb; font-size: 11px;")
                name_row.addWidget(ver_label)
                box_layout.addLayout(name_row)

                kw_label = QLabel(f"触发: {s['trigger_keywords']}")
                kw_label.setStyleSheet("color: #999; font-size: 12px;")
                box_layout.addWidget(kw_label)

                btn_row = QHBoxLayout()
                toggle_btn = QPushButton("禁用" if s['enabled'] else "启用")
                toggle_btn.setFixedWidth(70)
                toggle_btn.clicked.connect(lambda checked, sid=s['id'], en=s['enabled']: self._toggle_skill(sid, not en))
                del_btn = QPushButton("删除")
                del_btn.setStyleSheet("color: #f44336; padding: 6px 10px;")
                del_btn.setFixedWidth(70)
                del_btn.clicked.connect(lambda checked, sid=s['id']: self._delete_skill(sid))
                btn_row.addWidget(toggle_btn)
                btn_row.addWidget(del_btn)
                btn_row.addStretch()
                box_layout.addLayout(btn_row)

                layout.addWidget(skill_box)

        layout.addStretch()
        return page

    def _toggle_skill(self, skill_id: int, enabled: bool):
        from modules.self_evolution.skill_registry import SkillRegistry
        reg = SkillRegistry()
        reg.update(skill_id, enabled=1 if enabled else 0)
        self.stacked.removeWidget(self.stacked.widget(2))
        self.stacked.insertWidget(2, self._build_skill_page())
        self.stacked.setCurrentIndex(2)

    def _delete_skill(self, skill_id: int):
        reply = QMessageBox.question(self, "确认删除", "确定要删除这个技能吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            from modules.self_evolution.skill_registry import SkillRegistry
            reg = SkillRegistry()
            reg.delete(skill_id)
            self.stacked.removeWidget(self.stacked.widget(2))
            self.stacked.insertWidget(2, self._build_skill_page())
            self.stacked.setCurrentIndex(2)

    def _logout(self):
        from ui.login_ui import clear_session
        clear_session()
        self.reject()

    def _on_save(self):
        lang_map = {"自动检测": "auto", "中文": "zh", "日文": "ja", "英文": "en"}
        self.cfg = {
            "astrbot_api_key": self.api_key.text().strip(),
            "astrbot_url": self.api_url.text().strip(),
            "tts_speed": self.speed_slider.value() / 100,
            "tts_pitch": float(self.pitch_slider.value()),
            "tts_volume": self._pet_vol_slider.value(),
            "tts_emotion": self.emotion_combo.currentText(),
            "voice_lang": lang_map.get(self.voice_lang_combo.currentText(), "auto"),
            "bubble_lang": lang_map.get(self.bubble_lang_combo.currentText(), "auto"),
            "tts_voice": self.tts_model_combo.currentText(),
            "tts_mode": self.cfg.get("tts_mode", "api"),
            "llm_mode": self.cfg.get("llm_mode", "api"),
            "character_name": self.cfg.get("character_name", "小女仆"),
            "sound_source": self.clone_path_edit.text().strip() if hasattr(self, 'clone_path_edit') else "",
            "personality": self.personality_combo.currentText() if hasattr(self, 'personality_combo') else "温柔贴心",
            "personality_prompt": self.personality_prompt.text().strip() if hasattr(self, 'personality_prompt') else "",
            "user_title": self.user_title.text().strip() if hasattr(self, 'user_title') else "龙之介大人",
            "talk_style": self.talk_style_combo.currentText() if hasattr(self, 'talk_style_combo') else "正常",
            "window_x": -1, "window_y": -1,
        }
        uid = self.user.get('user_id', 0)
        if uid:
            cfg_to_db(uid, self.cfg)
        self.accepted = True
        self.accept()
