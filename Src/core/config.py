"""
桌宠配置 - 路径和常量
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 资源目录
RES_DIR = os.path.join(BASE_DIR, "resourses")
EXAMPLE_DIR = os.path.join(RES_DIR, "example")
BEHAVIORS_DIR = os.path.join(RES_DIR, "behaviors")
VOICES_DIR = os.path.join(RES_DIR, "voices")

# 动作帧目录
HELLO_DIR = os.path.join(BEHAVIORS_DIR, "Hello")
BYE_DIR = os.path.join(BEHAVIORS_DIR, "Bye")

# 素材路径
CHAR_PATH = os.path.join(EXAMPLE_DIR, "maid_static_character.png")
FACE_PATH = os.path.join(EXAMPLE_DIR, "maid_static_face.png")
SOUND_PATH = os.path.join(VOICES_DIR, "maid_sounds.mp3")

# 窗口尺寸
WIN_W, WIN_H = 200, 260

# 帧率
FPS = 30

# 行为映射: action -> (帧目录, 帧数)
BEHAVIORS = {
    "hello": {"dir": os.path.join(BEHAVIORS_DIR, "Hello"), "frames": 10, "loop": False},
    "idle":  {"dir": None, "frames": 0, "loop": True},
    "bye":   {"dir": os.path.join(BEHAVIORS_DIR, "Bye"), "frames": 0, "loop": False},
}
