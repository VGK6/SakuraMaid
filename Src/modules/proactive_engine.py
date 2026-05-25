"""
桌宠主动能力 — 定时器 + 环境感知 + 异常检测
"""
import threading, time, json, os
from datetime import datetime, timedelta

class ProactiveEngine:
    """桌宠主动能力引擎"""

    def __init__(self, pet_window=None):
        self.pet = pet_window
        self._running = False
        self._thread = None
        self._done_today = set()
        self._last_activity_time = time.time()
        self._last_cpu_warn = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("🧠 主动能力引擎已启动")

    def stop(self):
        self._running = False

    def _loop(self):
        """主循环：每30秒检查一次"""
        while self._running:
            try:
                now = datetime.now()
                today = now.strftime("%Y-%m-%d")

                # ── 定时任务 ──
                self._check_scheduled(now, today)

                # ── 环境感知 ──
                self._check_environment(now)

                # ── 异常检测 ──
                self._check_anomalies()

                # ── 清理过期记录 ──
                yesterday = (now - timedelta(days=2)).strftime("%Y-%m-%d")
                self._done_today = {t for t in self._done_today if yesterday not in t}

            except Exception as e:
                print(f"主动引擎异常: {e}")

            time.sleep(30)

    # ── 工具方法 ──

    def _bubble(self, text, duration=5000):
        if self.pet:
            try:
                self.pet._bubble_queue.put((text, duration))
            except:
                pass

    def _speak(self, text):
        """语音播报"""
        try:
            from modules.voice import speak
            threading.Thread(target=lambda: speak(text), daemon=True).start()
        except:
            pass

    def _mark_done(self, task_prefix: str, today: str, now=None):
        """标记任务已执行"""
        if now is None:
            now = datetime.now()
        key = f"{task_prefix}_{today}_{now.hour}"
        if key not in self._done_today:
            self._done_today.add(key)
            return True
        return False

    # ═══════════════════════════════════════
    #  ① 定时任务
    # ═══════════════════════════════════════

    def _check_scheduled(self, now, today):
        h, m = now.hour, now.minute

        # 07:00 → 天气
        if h == 7 and m == 0:
            if self._mark_done("weather", today):
                self._do_weather()

        # 08:00 → 动漫+学校
        if h == 8 and m == 0:
            if self._mark_done("daily", today):
                self._do_daily_info()

        # 22:30 → 休息提醒
        if h == 22 and m == 30:
            if self._mark_done("rest", today):
                self._do_rest_reminder()

        # 每30分钟 → 邮件
        if m % 30 == 0 and now.second < 5:
            if self._mark_done("mail", today):
                self._do_mail_check()

    def _do_weather(self):
        try:
            from modules.astrbot_client import chat
            reply = chat("查询今天杭州的天气")
            if reply:
                msg = f"☀️ 早安！{reply[:80]}"
                self._bubble(msg, 10000)
                self._speak(msg)
        except:
            self._bubble("☀️ 早上好！今天也要加油哦~", 5000)

    def _do_daily_info(self):
        try:
            from modules.astrbot_client import chat
            reply = chat("今天有什么动漫更新")
            if reply:
                msg = f"📺 {reply[:80]}"
                self._bubble(msg, 8000)
                self._speak(msg)
        except:
            self._bubble("📺 早安~", 3000)

    def _do_rest_reminder(self):
        msg = "🌙 龙之介大人，已经22:30了，该休息了~ 如果还在用电脑的话，记得早点睡哦！😊"
        self._bubble(msg, 10000)
        self._speak(msg)

    def _do_mail_check(self):
        try:
            from modules.scheduler import get_unread_mail
            mails = get_unread_mail()
            if mails:
                self._bubble(f"📧 您有{len(mails)}封新邮件", 5000)
        except:
            pass

    # ═══════════════════════════════════════
    #  ② 环境感知
    # ═══════════════════════════════════════

    def _check_environment(self, now):
        """环境感知：深夜提醒 + 无操作检测"""
        h = now.hour

        # 深夜检测 (0:00~5:00 还在电脑前)
        if 0 <= h <= 5:
            # 每小时提醒一次
            if self._mark_done("late_night", now.strftime("%Y-%m-%d"), now):
                msg = f"🌙 已经{now.hour}点多了，还不休息吗？熬夜对身体不好哦~"
                self._bubble(msg, 8000)
                self._speak(msg)

        # 长时间无操作检测 (2小时)
        idle_time = time.time() - self._last_activity_time
        if idle_time > 7200:  # 2小时
            self._last_activity_time = time.time()
            self._bubble("😴 龙之介大人，好久没动了，还在吗？", 5000)

    def record_activity(self):
        """记录用户活动（由pet_window调用）"""
        self._last_activity_time = time.time()

    # ═══════════════════════════════════════
    #  ③ 异常检测
    # ═══════════════════════════════════════

    def _check_anomalies(self):
        """异常检测：CPU/内存/磁盘预警"""
        try:
            import psutil

            # CPU温度过高
            cpu = psutil.cpu_percent(interval=0.1)
            if cpu > 85 and time.time() - self._last_cpu_warn > 300:  # 5分钟冷却
                self._last_cpu_warn = time.time()
                self._bubble(f"🔥 CPU使用率{cpu}%，有点高哦，要不要检查一下？", 6000)

            # 磁盘空间不足
            disk = psutil.disk_usage('/')
            if disk.free / disk.total < 0.05:  # 剩余<5%
                self._bubble(f"⚠️ C盘只剩{disk.free/1024**3:.0f}GB了，该清理了~", 8000)

            # 内存不足
            mem = psutil.virtual_memory()
            if mem.percent > 90:
                self._bubble(f"⚠️ 内存占用{mem.percent}%，建议关掉一些程序~", 6000)
        except:
            pass
