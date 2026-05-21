"""
系统监控 - 检测系统状态并自修复
"""
import psutil, os, subprocess, threading, time

class SystemMonitor:
    def __init__(self):
        self._alerts = []

    def get_cpu(self) -> float:
        """获取CPU使用率"""
        return psutil.cpu_percent(interval=0.5)

    def get_memory(self) -> dict:
        """获取内存信息"""
        mem = psutil.virtual_memory()
        return {"total": mem.total / 1e9, "used": mem.used / 1e9, "percent": mem.percent}

    def get_disk(self, path="C:") -> dict:
        """获取磁盘信息"""
        d = psutil.disk_usage(path)
        return {"total": d.total / 1e9, "used": d.used / 1e9, "free": d.free / 1e9, "percent": d.percent}

    def check_process(self, name: str) -> bool:
        """检查进程是否在运行"""
        for proc in psutil.process_iter(['name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def restart_process(self, name: str, path: str) -> bool:
        """重启指定进程"""
        try:
            subprocess.run(['taskkill', '/F', '/IM', name], capture_output=True)
            time.sleep(2)
            subprocess.Popen([path], shell=True)
            return True
        except:
            return False

    def full_check(self) -> list:
        """全面检查，返回异常列表"""
        alerts = []
        cpu = self.get_cpu()
        if cpu > 80:
            alerts.append(f"⚠️ CPU使用率 {cpu:.0f}%")
        mem = self.get_memory()
        if mem['percent'] > 85:
            alerts.append(f"⚠️ 内存使用 {mem['percent']:.0f}%")
        disk = self.get_disk()
        if disk['percent'] > 90:
            alerts.append(f"⚠️ C盘空间 {disk['free']:.1f}GB")
        return alerts
