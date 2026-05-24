"""
主窗口 - 桌宠渲染与交互
"""
import os, math, time, threading, queue
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon
from PySide6.QtCore import Qt, QTimer, QRect, QThread
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

from core.config import *
from core.animation import AnimationManager
from core.bubble import BubbleWindow
from modules.voice import speak
from modules.llm_client import chat
from modules.system_monitor import SystemMonitor
from modules.virtual_hand import VirtualHand
from modules.config_store import load as load_cfg, save as save_cfg
from modules.scheduler import get_schedule, get_unread_mail
from modules.speech_recognition import listen, is_listening
from modules.action_engine import ActionEngine
from modules.hotkey import register_hotkey
from core.bubble import BubbleWindow

class MaidPet(QWidget):
    def __init__(self, config: dict = None):
        super().__init__()
        self.user_cfg = config or {}
        self.monitor = SystemMonitor()
        self.hand = VirtualHand()
        self.action_engine = ActionEngine()
        self._bubble_queue = queue.Queue()  # 跨线程气泡队列
        self._bubble_win = BubbleWindow(self)  # 独立气泡窗口
        # 注册全局快捷键 Ctrl+Shift+V
        try:
            from PySide6.QtWidgets import QApplication
            register_hotkey(QApplication.instance(), self._start_voice_input)
        except Exception as e:
            print(f"快捷键注册失败: {e}")
        self._init_window()
        self._load_resources()
        self._init_state()
        self._init_timers()
        self._init_interaction()
        self._init_tray()
        self._init_checker()

        self.show()
        QTimer.singleShot(1000, self._greet)

    # ── 初始化 ──

    def _init_window(self):
        self.cfg = load_cfg()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(WIN_W, WIN_H)
        if self.cfg["window_x"] > 0 and self.cfg["window_y"] > 0:
            self.move(self.cfg["window_x"], self.cfg["window_y"])
        else:
            scr = QApplication.primaryScreen().geometry()
            self.move(scr.width() - 250, scr.height() - 350)

    def closeEvent(self, e):
        self.cfg["window_x"] = self.x()
        self.cfg["window_y"] = self.y()
        save_cfg(self.cfg)
        self.hide()
        e.ignore()

    def _load_resources(self):
        # 序列帧
        self.anim = AnimationManager()
        self.anim.load_behavior("hello", BEHAVIORS["hello"]["dir"])
        self.anim.load_behavior("bye", BEHAVIORS["bye"]["dir"])

        # 静态图
        self.char_pix = QPixmap(CHAR_PATH) if os.path.exists(CHAR_PATH) else QPixmap()
        if not self.char_pix.isNull():
            self.char_pix = self.char_pix.scaled(140, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 气泡
        self._bubble_win = BubbleWindow(self)  # 独立气泡窗口

    def _init_state(self):
        self.state = 'idle'
        self.frame_idx = 0.0
        self.float_y = 0.0
        self.bubble_text = ""
        self.speaking = False

    def _init_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000 // FPS)

    def _init_interaction(self):
        self.drag = False
        self.doff = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    # ── 主循环 ──

    def _tick(self):
        self.float_y = 3 * math.sin(time.time() * 2.5)

        if self.state == 'hello' and self.anim.has_frames('hello'):
            self.frame_idx += 0.15
            if self.frame_idx >= len(self.anim.get_frames('hello')):
                self.state = 'idle'
                self.frame_idx = 0

        self.update()

        # 处理跨线程气泡请求
        try:
            while True:
                text, dur = self._bubble_queue.get_nowait()
                self._show_bubble(text, dur)
        except queue.Empty:
            pass

    # ── 绘制 ──

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        fy = int(self.float_y)

        # 角色
        if self.state == 'hello' and self.anim.has_frames('hello'):
            frames = self.anim.get_frames('hello')
            idx = min(int(self.frame_idx), len(frames) - 1)
            frame = frames[idx].scaled(150, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            px = (WIN_W - frame.width()) // 2
            p.drawPixmap(px, 20 + fy, frame)
        elif not self.char_pix.isNull():
            px = (WIN_W - self.char_pix.width()) // 2
            p.drawPixmap(px, 20 + fy, self.char_pix)

        # 名字
        p.setPen(QColor(255, 120, 150))
        p.setFont(QFont('Microsoft YaHei', 10))
        p.drawText(QRect(0, WIN_H - 45, WIN_W, 25), Qt.AlignCenter, "🌸 小女仆")

        # 状态灯
        status_dot = "●"
        if self.state == 'hello':
            p.setPen(QColor(255, 200, 100))
        elif self.speaking:
            p.setPen(QColor(100, 200, 100))
        else:
            p.setPen(QColor(150, 150, 150))
        p.drawText(QRect(WIN_W - 30, 5, 25, 20), Qt.AlignCenter, status_dot)

        # 气泡改为独立窗口BubbleWindow，不再在窗口内绘制

    # ── 交互 ──

    def _greet(self):
        self.state = 'hello'
        self.frame_idx = 0
        self._show_bubble("龙之介大人，欢迎回来~🌸")
        threading.Thread(target=lambda: speak("龙之介大人，欢迎回来~"), daemon=True).start()

    def _chat(self):
        if self.speaking:
            return
        self.state = 'hello'
        self.frame_idx = 0
        self._show_bubble("💭 我在想...")
        threading.Thread(target=self._do_chat, daemon=True).start()

    def _do_chat(self):
        try:
            reply = chat("你好~")
            self._show_bubble(f"💬 {reply}")
            threading.Thread(target=lambda: speak(reply), daemon=True).start()
        except Exception as e:
            self._show_bubble(f"⚠️ {str(e)[:30]}")

    def _show_bubble(self, text, duration=3000):
        """线程安全的气泡显示（独立窗口）"""
        if QThread.currentThread() is not QApplication.instance().thread():
            self._bubble_queue.put((text, duration))
            return
        if text == "__clear__":
            self._bubble_win.hide()
            return
        self.bubble_text = text
        self._bubble_win.show_text(text, duration, self.pos())
        QTimer.singleShot(duration, self._clear_bubble)

    def _clear_bubble(self):
        self.bubble_text = ""
        self._bubble_win.hide()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag = True
            self.doff = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag:
            self.move(e.globalPosition().toPoint() - self.doff)

    def mouseReleaseEvent(self, e):
        self.drag = False

    def mouseDoubleClickEvent(self, e):
        self._start_voice_input()

    def enterEvent(self, e):
        if self.state == 'idle' and self.anim.has_frames('hello'):
            self.state = 'hello'
            self.frame_idx = 0
            QTimer.singleShot(1500, lambda: setattr(self, 'state', 'idle'))

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("🌸 小女仆")
        tray_menu = QMenu()
        tray_menu.addAction("🌸 显示", self.show)
        tray_menu.addAction("🙈 隐藏", self.hide)
        tray_menu.addSeparator()
        tray_menu.addAction("🎤 语音输入", self._start_voice_input)
        tray_menu.addAction("💬 文字对话", self._chat)
        tray_menu.addSeparator()
        tray_menu.addAction("⚙️ 设置", self._open_settings)
        tray_menu.addAction("🛡️ 系统检查", self._run_system_check)
        tray_menu.addSeparator()
        tray_menu.addAction("❌ 退出", QApplication.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()

    def _run_system_check(self):
        threading.Thread(target=self._do_system_check, daemon=True).start()

    def _do_system_check(self):
        time.sleep(2)
        alerts = self.monitor.full_check()
        cpu = self.monitor.get_cpu()
        mem = self.monitor.get_memory()
        disk = self.monitor.get_disk()
        msg = f"CPU: {cpu:.0f}% | 内存: {mem['percent']:.0f}% | C盘: {disk['free']:.1f}G"
        if alerts:
            msg += chr(10) + "⚠️ " + (chr(10)).join(alerts)
        else:
            msg += chr(10) + "✅ 一切正常"
        self._show_bubble(msg, 5000)

    def _start_voice_input(self):
        """启动语音输入（可从任意线程安全调用）"""
        if is_listening():
            self._bubble_queue.put(("🎤 正在录音中...", 2000))
            return
        self._bubble_queue.put(("🎤 聆听中，说完会自动停止...", 0))
        threading.Thread(target=self._do_voice_input, daemon=True).start()

    def _open_settings(self):
        """打开配置界面"""
        QTimer.singleShot(0, self._do_open_settings)

    def _do_open_settings(self):
        from ui.config_ui import ConfigUI, db_to_cfg
        self.hide()
        cfg_ui = ConfigUI(user={"user_id": 0, "username": "龙之介大人"})
        if cfg_ui.exec() == ConfigUI.Accepted:
            self.show()
        else:
            self.show()

    def _do_voice_input(self):
        # 先显示麦克风信息
        from modules.speech_recognition import list_devices, get_default_device
        try:
            default = get_default_device()
            print(f"🎤 麦克风: {default['name']}")
        except:
            pass

        self._show_bubble("🎤 聆听中，说完会自动停止...", 0)
        text = listen(timeout=10.0, silence_limit=2.0)
        
        self._clear_bubble()
        
        if not text:
            self._show_bubble("😶 没听清，双击再试一次？", 2500)
            return
        
        # 判断是否为操作指令
        action_keywords = ["打开", "关闭", "点击", "输入", "搜索", "滚动", "下载", "启动", "创建", "删除", "复制", "粘贴"]
        is_action = any(k in text for k in action_keywords)
        
        if is_action:
            self._show_bubble("🤔 正在分析并执行...", 2000)
            threading.Thread(target=self._do_action, args=(text,), daemon=True).start()
        else:
            # 普通对话
            from modules.astrbot_client import chat
            reply = chat(text)
            if reply:
                self._show_bubble(reply, 15000)  # 先显示15秒
                def _speak_and_sync():
                    dur = speak(reply)
                    if dur > 0:
                        # 语音播完，延后1秒清除气泡
                        import time
                        time.sleep(1)
                        self._bubble_queue.put(("__clear__", 0))
                    else:
                        self._bubble_queue.put(("__clear__", 5000))
                threading.Thread(target=_speak_and_sync, daemon=True).start()

    def _do_action(self, instruction: str):
        """执行操作指令"""
        result = self.action_engine.execute(instruction)
        if result["success"]:
            msg = f"✅ 完成! {result['summary']}"
        else:
            msg = f"❌ 失败: {result.get('error', '未知错误')}"
        dur = max(4000, min(10000, len(msg) * 120))
        self._show_bubble(msg, dur)
        from modules.voice import speak
        speak(msg)

    def _start_action_mode(self):
        """启动自动执行模式（语音输入→动作）"""
        self._show_bubble("🤖 请说出要执行的操作", 3000)
        threading.Thread(target=self._do_action_voice, daemon=True).start()

    def _do_action_voice(self):
        text = listen(timeout=8.0)
        if text:
            self._show_bubble(f"🤖 {text}", 2000)
            self._do_action(text)

    def _init_checker(self):
        """定时检查日程和邮件"""
        self._last_mail_count = 0
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._periodic_check)
        self.check_timer.start(30000)  # 每30秒检查一次

    def _periodic_check(self):
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        # 检查邮件
        try:
            mails = get_unread_mail()
            if len(mails) > self._last_mail_count:
                new = len(mails) - self._last_mail_count
                self._show_bubble(f"📧 {new}封新邮件！", 4000)
            self._last_mail_count = len(mails)
        except:
            pass
        
        # 检查定时任务
        try:
            import json, os
            from datetime import datetime
            ASTROB_DB = os.path.expanduser("~") + "/.astrbot/data/data_v4.db"
            TRIGGER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cron_trigger.json")
            
            # 加载触发记录
            triggers = {}
            if os.path.exists(TRIGGER_FILE):
                try:
                    with open(TRIGGER_FILE, "r") as f:
                        triggers = json.load(f)
                except:
                    pass
            
            import sqlite3
            conn = sqlite3.connect(ASTROB_DB)
            c = conn.cursor()
            c.execute("SELECT name, cron_expression FROM cron_jobs WHERE enabled=1")
            rows = c.fetchall()
            conn.close()
            
            now = datetime.now()
            now_key = now.strftime("%Y-%m-%d %H:%M")
            
            for name, cron in rows:
                if "SelfEvolution" in name:
                    continue
                if cron:
                    parts = cron.split()
                    if len(parts) >= 2:
                        cron_h, cron_m = parts[1], parts[0]
                        ch = str(now.hour)
                        cm = str(now.minute)
                        if (cron_h == ch or cron_h == "*") and \
                           (cron_m == cm or cron_m == "*"):
                            last = triggers.get(name, "")
                            today = now.strftime("%Y-%m-%d")
                            if not last.startswith(today):
                                triggers[name] = now_key
                                with open(TRIGGER_FILE, "w") as f:
                                    json.dump(triggers, f)
                                self._show_bubble(f"⏰ {name}", 5000)
        except:
            pass

    def _show_schedule(self):
        tasks = get_schedule()
        if not tasks:
            self._show_bubble("📋 暂无定时任务", 2000)
            return
        msg = "📋 今日日程:" + chr(10)
        for t in tasks:
            msg += f"  {t['name']} ({t['cron']})" + chr(10)
        self._show_bubble(msg.strip(), 5000)

    def _show_mail(self):
        mails = get_unread_mail()
        if not mails:
            self._show_bubble("📭 暂无未读邮件", 2000)
            return
        msg = f"📧 {len(mails)}封未读:" + chr(10)
        for m in mails:
            msg += f"  {m['subject'][:25]}" + chr(10)
        self._show_bubble(msg.strip(), 5000)

    def _show_menu(self, pos):
        m = QMenu(self)
        m.addAction("🎤 语音输入", self._start_voice_input)
        m.addAction("💬 说句话", self._chat)
        m.addSeparator()
        m.addAction("🛡️ 系统检查", self._run_system_check)
        m.addAction("⚙️ 设置", self._open_settings)
        m.addSeparator()
        m.addAction("🚪 退出", QApplication.quit)
        m.exec(self.mapToGlobal(pos))
