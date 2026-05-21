"""
虚拟手 - 模拟鼠标和键盘输入
"""
import pyautogui, time

pyautogui.FAILSAFE = False

class VirtualHand:
    """模拟鼠标键盘操作的虚拟手"""

    @staticmethod
    def click(x: int = None, y: int = None, button: str = "left"):
        """鼠标点击"""
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)
        time.sleep(0.1)

    @staticmethod
    def double_click(x: int = None, y: int = None):
        """双击"""
        if x and y:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()

    @staticmethod
    def right_click(x: int = None, y: int = None):
        """右键"""
        VirtualHand.click(x, y, button="right")

    @staticmethod
    def move(x: int, y: int, duration: float = 0.3):
        """移动鼠标到指定位置"""
        pyautogui.moveTo(x, y, duration=duration)

    @staticmethod
    def type_text(text: str, interval: float = 0.05):
        """模拟键盘输入文字"""
        pyautogui.typewrite(text, interval=interval)

    @staticmethod
    def hotkey(*keys):
        """模拟快捷键，如 hotkey('ctrl', 'c')"""
        pyautogui.hotkey(*keys)

    @staticmethod
    def scroll(clicks: int):
        """滚动鼠标滚轮"""
        pyautogui.scroll(clicks)

    @staticmethod
    def drag(from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5):
        """拖拽"""
        pyautogui.drag(to_x - from_x, to_y - from_y, duration=duration)

    @staticmethod
    def screenshot(region: tuple = None) -> str:
        """截图并保存"""
        path = "D:\\AstrBot\\Projects_user\\hand_screenshot.png"
        img = pyautogui.screenshot(region=region)
        img.save(path)
        return path

    @staticmethod
    def locate_image(image_path: str, confidence: float = 0.8):
        """在屏幕上查找图片位置"""
        result = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        return result  # 返回 (x, y) 或 None
