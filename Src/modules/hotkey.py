"""
全局快捷键模块 — Qt事件循环 + WinAPI RegisterHotKey
不需要管理员权限，能集成到桌宠的Qt事件循环中
"""
import ctypes, ctypes.wintypes
from PySide6.QtCore import QAbstractNativeEventFilter

WM_HOTKEY = 0x0312
MOD_CTRL = 0x0002
MOD_SHIFT = 0x0004
VK_V = 0x56

_on_trigger = None
_filter = None

class HotkeyFilter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, event_type, message):
        if event_type == b'windows_generic_MSG' or event_type == 'windows_generic_MSG':
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY and _on_trigger:
                import threading
                threading.Thread(target=_on_trigger, daemon=True).start()
                return True, 0
        return False, 0

def register_hotkey(app, callback):
    """注册全局快捷键 Ctrl+Shift+V，需要传入QApplication实例"""
    global _on_trigger, _filter
    
    if _filter is not None:
        return True
    
    _on_trigger = callback
    
    try:
        # 注册系统热键 (无需管理员权限)
        result = ctypes.windll.user32.RegisterHotKey(0, 1, MOD_CTRL | MOD_SHIFT, VK_V)
        if not result:
            print("⚠️ 系统热键注册失败")
            return False
        
        # 安装Qt事件过滤器
        _filter = HotkeyFilter()
        app.installNativeEventFilter(_filter)
        
        print("⌨️ 全局快捷键: Ctrl+Shift+V")
        return True
    except Exception as e:
        print(f"⚠️ 快捷键注册失败: {e}")
        return False

def unregister_hotkey():
    global _filter
    try:
        ctypes.windll.user32.UnregisterHotKey(0, 1)
    except:
        pass
    _filter = None
