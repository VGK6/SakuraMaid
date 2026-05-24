"""
屏幕捕获模块 — 基于pyautogui+PIL（无需OpenCV）
"""
import os
import numpy as np
from PIL import Image
import pyautogui
import threading, time

class ScreenCapture:
    def __init__(self):
        self._running = False
        self._last_frame = None
        self._thread = None

    def screenshot(self) -> Image.Image:
        """截取当前屏幕，返回PIL图像"""
        return pyautogui.screenshot()

    def screenshot_np(self) -> np.ndarray:
        """截取当前屏幕，返回numpy数组 (RGB)"""
        return np.array(self.screenshot())

    def save_screenshot(self, path: str = None) -> str:
        """截图并保存到文件（默认存到项目temp目录）"""
        if path is None:
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "resourses", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            path = os.path.join(temp_dir, "screenshot.png")
        self.screenshot().save(path)
        return path

    def get_active_window_info(self) -> dict:
        """获取当前活动窗口信息"""
        try:
            import pygetwindow as gw
            win = gw.getActiveWindow()
            if win:
                return {
                    "title": win.title,
                    "left": win.left, "top": win.top,
                    "width": win.width, "height": win.height,
                }
        except:
            pass
        return {"title": "未知", "width": 0, "height": 0}

    def capture_active_window(self) -> Image.Image:
        """截取当前活动窗口画面"""
        info = self.get_active_window_info()
        if info["width"] > 0 and info["height"] > 0:
            return pyautogui.screenshot(region=(info["left"], info["top"],
                                                info["width"], info["height"]))
        return self.screenshot()

    def detect_changes(self, threshold: float = 0.05) -> bool:
        """检测屏幕是否有显著变化（基于像素差异）"""
        current = np.array(self.screenshot())
        if self._last_frame is None:
            self._last_frame = current
            return False
        diff = np.abs(current.astype(int) - self._last_frame.astype(int))
        change_ratio = np.sum(diff > 30) / diff.size
        self._last_frame = current
        return change_ratio > threshold

    def get_foreground_color(self) -> str:
        """获取屏幕主色调描述"""
        img = np.array(self.screenshot())
        avg = img.mean(axis=(0, 1))
        r, g, b = avg
        if r > 200 and g > 200 and b > 200:
            return "亮色"
        elif r < 50 and g < 50 and b < 50:
            return "暗色"
        colors = [(r, "红色"), (g, "绿色"), (b, "蓝色")]
        colors.sort(reverse=True)
        return f"{colors[0][1]}调"

    def start_monitoring(self, callback, interval: float = 5.0):
        """启动屏幕监控"""
        self._running = True
        def _run():
            while self._running:
                try:
                    changed = self.detect_changes()
                    win_info = self.get_active_window_info()
                    if changed:
                        callback(win_info)
                except:
                    pass
                time.sleep(interval)
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self._running = False
