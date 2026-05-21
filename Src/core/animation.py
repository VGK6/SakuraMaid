"""
动作管理器 - 加载和管理序列帧
"""
import os
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class AnimationManager:
    def __init__(self):
        self._frames = {}  # {name: [QPixmap, ...]}

    def load_behavior(self, name: str, dir_path: str):
        """从目录加载动作帧"""
        if not dir_path or not os.path.exists(dir_path):
            self._frames[name] = []
            return
        files = sorted([f for f in os.listdir(dir_path) if f.endswith('.png')])
        frames = []
        for f in files:
            pix = QPixmap(os.path.join(dir_path, f))
            if not pix.isNull():
                frames.append(pix)
        self._frames[name] = frames
        print(f"  [{name}] 加载 {len(frames)} 帧")

    def get_frames(self, name: str):
        return self._frames.get(name, [])

    def has_frames(self, name: str) -> bool:
        return len(self._frames.get(name, [])) > 0
