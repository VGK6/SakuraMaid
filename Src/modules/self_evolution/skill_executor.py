"""
执行引擎 — 安全执行生成的技能代码
"""
import sys, os, traceback, time, json, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# 危险API清单
DANGEROUS_PATTERNS = [
    (r'os\.remove\s*\(', '文件删除操作'),
    (r'os\.unlink\s*\(', '文件删除操作'),
    (r'os\.rmdir\s*\(', '目录删除操作'),
    (r'shutil\.rmtree\s*\(', '递归删除操作'),
    (r'os\.system\s*\(', '系统命令执行'),
    (r'subprocess\.(call|Popen|run)\s*\(', '子进程执行'),
    (r'eval\s*\(', '动态代码执行'),
    (r'exec\s*\(', '动态代码执行'),
    (r'__import__\s*\(', '动态导入'),
    (r'ctypes\.', '底层系统调用'),
    (r'winreg\.', '注册表操作'),
]

# 路径白名单
ALLOWED_PATHS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Documents"),
]

class SkillExecutor:
    """安全执行技能"""

    def __init__(self, skill_registry=None):
        self.registry = skill_registry

    def scan_code(self, code: str) -> list:
        """静态安全检查，返回风险列表"""
        risks = []
        for pattern, desc in DANGEROUS_PATTERNS:
            import re
            if re.search(pattern, code):
                risks.append(desc)
        # 检查路径操作是否在白名单内
        if 'open(' in code and 'w' in code:
            for path in ALLOWED_PATHS:
                if path not in code:
                    risks.append(f"文件写入操作（路径需在白名单内: {ALLOWED_PATHS[0]}）")
                    break
        return risks

    def execute(self, code: str, skill_id: int = 0, user_confirm: bool = False) -> dict:
        """执行技能代码"""
        risks = self.scan_code(code)
        
        # 高风险操作需要确认
        high_risk = any(r in str(risks) for r in ['删除', '系统命令', '动态代码'])
        if high_risk and not user_confirm:
            return {"success": False, "error": "高危操作需用户确认", "risks": risks}
        
        start = time.time()
        try:
            # 在子进程中执行（限制资源）
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                tmp_path = f.name
            
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}
            )
            os.unlink(tmp_path)
            
            duration = int((time.time() - start) * 1000)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if self.registry:
                    self.registry.log(skill_id, True, duration)
                return {"success": True, "output": output, "duration_ms": duration}
            else:
                error = result.stderr.strip() or "执行失败"
                if self.registry:
                    self.registry.log(skill_id, False, duration, error)
                return {"success": False, "error": error, "duration_ms": duration}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "执行超时(>30秒)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
