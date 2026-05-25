"""
原子技能库 — 内置基础技能，无需LLM
"""
import os, datetime, subprocess, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

ATOMIC_SKILLS = [
    {
        "name": "获取当前时间",
        "keywords": ["现在几点", "当前时间", "几点了", "什么时间"],
        "priority": 100,
        "code": "import datetime; print(f'现在 {datetime.datetime.now().strftime(\"%H:%M\")}')",
    },
    {
        "name": "获取当前日期",
        "keywords": ["今天几号", "今天日期", "什么日期", "今天周几"],
        "priority": 100,
        "code": "import datetime; print(f'今天 {datetime.datetime.now().strftime(\"%Y年%m月%d日 %A\")}')",
    },
    {
        "name": "列出桌面文件",
        "keywords": ["查看桌面", "桌面文件", "显示桌面"],
        "priority": 90,
        "code": ("import os; path=os.path.expanduser('~/Desktop'); "
                 "files=[f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]; "
                 "print(f'桌面有{len(files)}个文件'); print('\\n'.join(files[:20]))"),
    },
    {
        "name": "创建空文件",
        "keywords": ["新建文件", "创建文件", "新文件"],
        "priority": 80,
        "code": ("import os; path=os.path.expanduser('~/Desktop'); "
                 "fname='new_file.txt'; fp=os.path.join(path,fname); "
                 "open(fp,'w').close(); print(f'已创建: {fp}')"),
    },
    {
        "name": "打开文件夹",
        "keywords": ["打开文件夹", "打开目录", "打开桌面"],
        "priority": 80,
        "code": ("import os, subprocess; "
                 "subprocess.run(['start', os.path.expanduser('~/Desktop')], shell=True); "
                 "print('已打开桌面文件夹')"),
    },
    {
        "name": "复制文件",
        "keywords": ["复制文件", "拷贝文件"],
        "priority": 70,
        "code": ("import shutil; "
                 "shutil.copy2('~/Desktop/source.txt', '~/Desktop/dest.txt'); "
                 "print('已复制')"),
    },
]

def get_all() -> list:
    return ATOMIC_SKILLS

def match(text: str) -> dict:
    """匹配原子技能"""
    tl = text.lower().strip()
    for s in ATOMIC_SKILLS:
        for kw in s["keywords"]:
            if kw in tl:
                return s
    return {}

def register_all(registry):
    """注册所有原子技能到技能表"""
    from modules.self_evolution.skill_registry import SkillRegistry
    for s in ATOMIC_SKILLS:
        registry.register(s["name"], s["keywords"], s["code"], s["priority"])
