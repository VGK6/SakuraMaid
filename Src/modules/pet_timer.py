"""
桌宠自带定时器 — 不依赖外部调度器，桌宠自己管自己
"""
import threading, time, json, os
from datetime import datetime, timedelta

class PetTimer:
    """桌宠内置定时器"""

    def __init__(self, pet_window=None):
        self.pet = pet_window
        self._running = False
        self._thread = None
        # 记录今天已执行过的任务
        self._done_today = set()

    def start(self):
        """启动定时器（后台线程）"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("⏰ 桌宠定时器已启动")

    def stop(self):
        self._running = False

    def _loop(self):
        """主循环：每30秒检查一次时间"""
        while self._running:
            try:
                now = datetime.now()
                today = now.strftime("%Y-%m-%d")
                key = f"{today}"

                # 07:00 → 天气推送
                if now.hour == 7 and now.minute == 0:
                    task = f"weather_{today}"
                    if task not in self._done_today:
                        self._done_today.add(task)
                        self._do_weather()

                # 08:00 → 动漫更新 + 学校信息
                if now.hour == 8 and now.minute == 0:
                    for task_name in ["anime", "school"]:
                        task = f"{task_name}_{today}"
                        if task not in self._done_today:
                            self._done_today.add(task)
                    self._do_daily_info()

                # 22:30 → 休息提醒
                if now.hour == 22 and now.minute == 30:
                    task = f"rest_{today}"
                    if task not in self._done_today:
                        self._done_today.add(task)
                        self._do_rest_reminder()

                # 每30分钟 → 邮件检查
                if now.minute % 30 == 0 and now.second < 10:
                    task = f"mail_{today}_{now.hour}_{now.minute}"
                    if task not in self._done_today:
                        self._done_today.add(task)
                        self._do_mail_check()

                # 清理过期记录（只保留最近2天）
                yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
                self._done_today = {t for t in self._done_today if yesterday not in t}

            except:
                pass

            time.sleep(30)

    def _bubble(self, text, duration=5000):
        """安全显示气泡"""
        if self.pet:
            try:
                self.pet._bubble_queue.put((text, duration))
            except:
                pass

    # ── 任务执行 ──

    def _do_weather(self):
        """查询天气并推送"""
        try:
            from modules.vision import describe_screen  # 复用llava连接
            import urllib.request, json
            req = urllib.request.Request("http://127.0.0.1:6185/api/tools/weather?city=杭州")
            # 直接通过AstrBot的天气工具
            self._bubble("☀️ 早上好！正在查今天的天气...", 3000)
            
            # 调用天气查询
            from modules.astrbot_client import chat
            reply = chat("查询今天杭州的天气")
            if reply:
                msg = f"☀️ 早安！{reply[:100]}"
                self._bubble(msg, 10000)
                from modules.voice import speak
                threading.Thread(target=lambda: speak(msg), daemon=True).start()
        except:
            self._bubble("☀️ 早上好！今天也要加油哦~", 5000)

    def _do_daily_info(self):
        """查询动漫更新和学校信息"""
        try:
            from modules.astrbot_client import chat
            # 动漫
            reply = chat("今天有什么动漫更新")
            msg = f"📺 早上好！{reply[:80]}"
            self._bubble(msg, 8000)
            from modules.voice import speak
            threading.Thread(target=lambda: speak(msg), daemon=True).start()
        except:
            self._bubble("📺 早上好！新的一天开始了~", 5000)

    def _do_rest_reminder(self):
        """22:30休息提醒"""
        msg = "🌙 龙之介大人，已经22:30了，该休息了~ 如果还在用电脑的话，记得早点睡哦！😊"
        self._bubble(msg, 10000)
        from modules.voice import speak
        threading.Thread(target=lambda: speak(msg), daemon=True).start()

    def _do_mail_check(self):
        """检查新邮件"""
        try:
            from modules.scheduler import get_unread_mail
            mails = get_unread_mail()
            if mails:
                self._bubble(f"📧 您有{len(mails)}封新邮件", 5000)
        except:
            pass
