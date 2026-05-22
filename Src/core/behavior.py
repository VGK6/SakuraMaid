"""
行为管理器 — 根据对话状态自动切换桌宠动作
支持序列帧 + 程序化动画（缩放/抖动/弹跳/呼吸）
"""
import os, random, math
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QTransform

# ── 行为定义 ──
BEHAVIORS = {
    "idle": {
        "type": "breath",       # 呼吸浮动
        "frames": [],           # 无需序列帧
        "speed": 1.0,
        "loop": True,
        "duration": 3000,
    },
    "hello": {
        "type": "sequence",     # 序列帧播放
        "frames": [],           # 运行时从Hello目录加载
        "speed": 1.0,
        "loop": False,
        "duration": 1500,
    },
    "talking": {
        "type": "bounce",       # 说话弹跳
        "frames": [],
        "speed": 2.0,
        "loop": True,
        "duration": 500,
    },
    "listening": {
        "type": "tilt",         # 侧耳倾听
        "frames": [],
        "speed": 1.0,
        "loop": True,
        "duration": 800,
    },
    "thinking": {
        "type": "shake",        # 歪头思考
        "frames": [],
        "speed": 0.5,
        "loop": False,
        "duration": 1200,
    },
    "happy": {
        "type": "jump",         # 开心跳
        "frames": [],
        "speed": 1.5,
        "loop": False,
        "duration": 1000,
    },
    "sad": {
        "type": "droop",        # 垂头丧气
        "frames": [],
        "speed": 0.5,
        "loop": False,
        "duration": 1500,
    },
    "confirm": {
        "type": "nod",          # 点头
        "frames": [],
        "speed": 1.2,
        "loop": False,
        "duration": 600,
    },
}


class BehaviorController:
    """控制桌宠的表情和动作"""

    def __init__(self, pet_widget):
        self.pet = pet_widget          # MaidPet窗口引用
        self.current = "idle"
        self._anim_timer = None
        self._breath_offset = 0
        self._bounce_offset = 0

    def set_behavior(self, name: str):
        """切换动作"""
        if name not in BEHAVIORS:
            name = "idle"
        self.current = name
        bhv = BEHAVIORS[name]
        btype = bhv["type"]

        if btype == "sequence":
            self._play_sequence(bhv)
        elif btype == "breath":
            self._start_procedural("breath")
        elif btype == "bounce":
            self._start_procedural("bounce")
        elif btype == "tilt":
            self._play_tilt()
        elif btype == "shake":
            self._play_shake()
        elif btype == "jump":
            self._play_jump()
        elif btype == "droop":
            self._play_droop()
        elif btype == "nod":
            self._play_nod()

    # ── 序列帧动画 ──
    def _play_sequence(self, bhv: dict):
        """播放序列帧动画"""
        frames = bhv.get("frames", [])
        if not frames:
            return
        self.pet.frame_idx = 0
        self.pet.frames = frames
        duration = bhv.get("duration", 1500)
        interval = max(50, duration // len(frames))
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._next_frame)
        self._anim_timer.start(interval)

    def _next_frame(self):
        self.pet.frame_idx += 1
        if self.pet.frame_idx >= len(self.pet.frames):
            self._anim_timer.stop()
            self.pet.frame_idx = 0
            if self.current == "hello":
                self.set_behavior("idle")

    # ── 程序化动画 ──
    def _start_procedural(self, ptype: str, duration: int = 3000):
        """启动程序化动画（呼吸/弹跳）"""
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._procedural_type = ptype
        self._breath_offset = 0
        self._anim_timer.timeout.connect(self._update_procedural)
        self._anim_timer.start(50)

    def _update_procedural(self):
        self._breath_offset += 0.1
        if self._procedural_type == "breath":
            # 呼吸：Y轴上下浮动 + 轻微缩放
            offset = math.sin(self._breath_offset) * 3
            scale = 1.0 + math.sin(self._breath_offset * 1.5) * 0.02
            self.pet.move(self.pet.x(), self.pet.y() + offset * 0.1)  # 微调
        elif self._procedural_type == "bounce":
            # 说话弹跳
            jump = abs(math.sin(self._breath_offset * 3)) * 5
            self.pet.move(self.pet.x(), self.pet.y() + jump * 0.1)

    def _play_tilt(self):
        """侧耳倾听：倾斜几度再回正"""
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._tilt_step = 0
        self._anim_timer.timeout.connect(self._update_tilt)
        self._anim_timer.start(50)

    def _update_tilt(self):
        self._tilt_step += 1
        if self._tilt_step < 10:
            angle = self._tilt_step * 2
        elif self._tilt_step < 20:
            angle = (20 - self._tilt_step) * 2
        else:
            self._anim_timer.stop()
            self.set_behavior("idle")
            return
        self.pet.set_rotation(angle) if hasattr(self.pet, 'set_rotation') else None

    def _play_shake(self):
        """思考：左右轻微摇晃"""
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._shake_step = 0
        self._anim_timer.timeout.connect(self._update_shake)
        self._anim_timer.start(80)

    def _update_shake(self):
        self._shake_step += 1
        if self._shake_step > 15:
            self._anim_timer.stop()
            self.set_behavior("idle")
            return
        offset = math.sin(self._shake_step * 1.5) * 4
        self.pet.move(self.pet.x() + offset * 0.1, self.pet.y())

    def _play_jump(self):
        """开心跳"""
        self._jump_height = 0
        self._jump_dir = -1
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._update_jump)
        self._anim_timer.start(30)

    def _update_jump(self):
        self._jump_height += self._jump_dir * 3
        if self._jump_height < -30:
            self._jump_dir = 1
        elif self._jump_height > 0:
            self._jump_dir = -1
            self._anim_timer.stop()
            self.set_behavior("idle")
            return
        self.pet.move(self.pet.x(), self.pet.y() - self._jump_height * 0.1)

    def _play_droop(self):
        """垂头"""
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._droop_step = 0
        self._anim_timer.timeout.connect(self._update_droop)
        self._anim_timer.start(50)

    def _update_droop(self):
        self._droop_step += 1
        if self._droop_step > 20:
            self._anim_timer.stop()
            self.set_behavior("idle")
            return

    def _play_nod(self):
        """点头"""
        if self._anim_timer:
            self._anim_timer.stop()
        self._anim_timer = QTimer()
        self._nod_step = 0
        self._anim_timer.timeout.connect(self._update_nod)
        self._anim_timer.start(50)

    def _update_nod(self):
        self._nod_step += 1
        if self._nod_step < 5:
            pass
        elif self._nod_step < 10:
            pass
        elif self._nod_step < 15:
            pass
        else:
            self._anim_timer.stop()
            self.set_behavior("idle")

    def stop(self):
        if self._anim_timer:
            self._anim_timer.stop()
