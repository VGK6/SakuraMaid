#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
樱花庄小女仆 · 桌宠 v1.0
MVP版 - PySide6 + 序列帧动画 + LLM对话 + TTS语音
"""

import sys, os, json, math, random, time, threading, tempfile, asyncio, urllib.request

from PySide6.QtWidgets import QApplication, QWidget, QMenu
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics, QPainterPath

# ====== 路径配置 ======
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resourses")
HELLO_DIR = os.path.join(BASE, "behaviors", "Hello")
CHAR_PATH = os.path.join(BASE, "example", "maid_static_character.png")
FACE_PATH = os.path.join(BASE, "example", "maid_static_face.png")
SOUND_PATH = os.path.join(BASE, "voices", "maid_sounds.mp3")

# ====== TTS ======
_tts_loop = None
def tts(text, out_path):
    global _tts_loop
    if _tts_loop is None:
        _tts_loop = asyncio.new_event_loop()
        threading.Thread(target=_tts_loop.run_forever, daemon=True).start()
    import edge_tts
    future = asyncio.run_coroutine_threadsafe(
        edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural").save(out_path), _tts_loop)
    future.result(timeout=30)

# ====== LLM ======
# 从环境变量读取API Key，不要硬编码在代码里！
import os
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_KEY:
    print("⚠️ 请设置环境变量 DEEPSEEK_API_KEY")
    DEEPSEEK_KEY = "YOUR_KEY_HERE"
def llm(text):
    data = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role":"system","content":"你是樱花庄的小女仆AI，简短可爱地回答，不超过20字。"},
            {"role":"user","content":text}
        ],
        "max_tokens": 200
    }).encode()
    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
        data=data, headers={"Content-Type":"application/json",
        "Authorization":f"Bearer {DEEPSEEK_KEY}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]

# ====== 播放语音 ======
def play_audio(path):
    import soundfile as sf, sounddevice as sd
    data, sr = sf.read(path)
    sd.play(data, sr)
    sd.wait()

# ====== 主窗口 ======
class MaidPet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(200, 260)

        # 加载序列帧
        self.hello_frames = []
        if os.path.exists(HELLO_DIR):
            files = sorted([f for f in os.listdir(HELLO_DIR) if f.endswith('.png')])
            for f in files:
                pix = QPixmap(os.path.join(HELLO_DIR, f))
                if not pix.isNull():
                    self.hello_frames.append(pix)
        print(f"加载 {len(self.hello_frames)} 帧 Hello 动作")

        # 加载静态角色图
        self.char_pix = QPixmap(CHAR_PATH) if os.path.exists(CHAR_PATH) else QPixmap()
        if not self.char_pix.isNull():
            self.char_pix = self.char_pix.scaled(140, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 动画状态
        self.state = 'idle'       # idle / hello / talk / think
        self.frame_idx = 0.0
        self.float_y = 0.0
        self.bubble_text = ""
        self.speaking = False

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)  # ~30fps

        # 位置 - 右下角
        scr = QApplication.primaryScreen().geometry()
        self.move(scr.width() - 250, scr.height() - 350)

        # 交互
        self.drag = False
        self.doff = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

        self.show()

        # 启动问候
        QTimer.singleShot(1000, self._greet)

    def tick(self):
        # 浮动呼吸
        self.float_y = 3 * math.sin(time.time() * 2.5)

        # 帧动画
        if self.state == 'hello' and self.hello_frames:
            self.frame_idx += 0.15
            if self.frame_idx >= len(self.hello_frames):
                self.state = 'idle'
                self.frame_idx = 0

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        fy = int(self.float_y)

        if self.state == 'hello' and self.hello_frames:
            # 播放挥手动画
            idx = min(int(self.frame_idx), len(self.hello_frames) - 1)
            frame = self.hello_frames[idx].scaled(150, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            px = (200 - frame.width()) // 2
            py = 20 + fy
            p.drawPixmap(px, py, frame)
        elif not self.char_pix.isNull():
            # 待机显示角色图
            px = (200 - self.char_pix.width()) // 2
            py = 20 + fy
            p.drawPixmap(px, py, self.char_pix)

        # 名字标签
        p.setPen(QColor(255, 120, 150))
        p.setFont(QFont('Microsoft YaHei', 10))
        p.drawText(QRect(0, 215, 200, 25), Qt.AlignCenter, "🌸 小女仆")

        # 状态指示
        status_dot = "●"
        if self.state == 'hello':
            p.setPen(QColor(255, 200, 100))
        elif self.speaking:
            p.setPen(QColor(100, 200, 100))
        else:
            p.setPen(QColor(150, 150, 150))
        p.drawText(QRect(170, 5, 25, 20), Qt.AlignCenter, status_dot)

        # 气泡
        if self.bubble_text:
            self._draw_bubble(p)

    def _draw_bubble(self, p):
        font = QFont('Microsoft YaHei', 11)
        p.setFont(font)
        fm = QFontMetrics(font)
        lines, line = [], ""
        for ch in self.bubble_text:
            t = line + ch
            if fm.horizontalAdvance(t) > 200:
                lines.append(line); line = ch
            else: line = t
        if line: lines.append(line)
        lh = fm.height() + 4
        bw, bh = 220, len(lines) * lh + 20
        bx, by = 100 - bw//2, -bh - 5
        path = QPainterPath()
        path.addRoundedRect(bx, by, bw, bh, 10, 10)
        p.fillPath(path, QColor(255, 255, 255, 235))
        p.setPen(QColor(200, 200, 200))
        p.drawPath(path)
        ax, ay = 100, by + bh
        tri = QPainterPath()
        tri.moveTo(ax-6, ay); tri.lineTo(ax, ay+8); tri.lineTo(ax+6, ay)
        tri.closeSubpath()
        p.fillPath(tri, QColor(255, 255, 255, 235))
        p.drawPath(tri)
        p.setPen(QColor(50, 50, 50))
        for i, l in enumerate(lines):
            p.drawText(bx+10, by+14 + i*lh, l)

    # ====== 交互 ======

    def _greet(self):
        self.state = 'hello'
        self.frame_idx = 0
        self.bubble_text = "龙之介大人，欢迎回来~🌸"
        # 播放问候语音
        threading.Thread(target=self._speak, args=("龙之介大人，欢迎回来~",), daemon=True).start()
        QTimer.singleShot(3000, self._clear_bubble)

    def _clear_bubble(self):
        self.bubble_text = ""

    def _speak(self, text):
        self.speaking = True
        try:
            tmp = os.path.join(tempfile.gettempdir(), "pet_tts.mp3")
            tts(text, tmp)
            play_audio(tmp)
        except:
            pass
        self.speaking = False

    def _chat(self):
        if self.speaking:
            return
        self.state = 'hello'
        self.frame_idx = 0
        self.bubble_text = "💭 我在想..."
        self.update()

        def do_chat():
            try:
                reply = llm("你好~")
                self.bubble_text = f"💬 {reply}"
                self.update()
                threading.Thread(target=self._speak, args=(reply,), daemon=True).start()
                QTimer.singleShot(4000, self._clear_bubble)
            except Exception as e:
                self.bubble_text = f"⚠️ {str(e)[:30]}"
                self.update()
                QTimer.singleShot(2000, self._clear_bubble)

        threading.Thread(target=do_chat, daemon=True).start()

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
        self._chat()

    def enterEvent(self, e):
        if self.state == 'idle' and self.hello_frames:
            self.state = 'hello'
            self.frame_idx = 0
            QTimer.singleShot(1500, lambda: setattr(self, 'state', 'idle'))

    def _menu(self, pos):
        m = QMenu(self)
        m.addAction("👋 打招呼", self._greet)
        m.addAction("💬 说句话", self._chat)
        m.addAction("😊 开心", lambda: self._set_bubble("嘿嘿~(*^▽^*)"))
        m.addSeparator()
        m.addAction("📋 关于", lambda: self._set_bubble("樱花庄小女仆 v1.0\n为龙之介大人定制"))
        m.addSeparator()
        m.addAction("🚪 退出", QApplication.quit)
        m.exec(self.mapToGlobal(pos))

    def _set_bubble(self, text):
        self.bubble_text = text
        QTimer.singleShot(3000, self._clear_bubble)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = MaidPet()
    sys.exit(app.exec())
