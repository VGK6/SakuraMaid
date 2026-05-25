"""
错误诊疗室 — 捕获异常→分析原因→自修复
"""
import sys, os, json, re, traceback
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

class ErrorHealer:
    """错误诊断与自愈"""

    MAX_RETRIES = 3

    def __init__(self, registry=None):
        self.registry = registry
        self._retry_count = 0

    def heal(self, error: str, code: str, skill_id: int = 0) -> dict:
        """
        诊疗入口：查经验库→LLM分析→修复→重试
        返回: {"healed": bool, "fixed_code": str, "message": str}
        """
        self._retry_count = 0
        return self._heal_loop(error, code, skill_id)

    def _heal_loop(self, error: str, code: str, skill_id: int = 0) -> dict:
        """修复循环（最多3次）"""
        while self._retry_count < self.MAX_RETRIES:
            self._retry_count += 1
            
            # 1. 查修复经验库
            if self.registry:
                known = self.registry.find_fix(error)
                if known:
                    fix_code = known['solution_code']
                    result = self._try_fix(fix_code, skill_id)
                    if result.get("success"):
                        return {"healed": True, "fixed_code": fix_code, 
                                "message": f"经验库修复成功", "retries": self._retry_count}
            
            # 2. LLM分析修复
            fix = self._llm_analyze(error, code)
            if not fix.get("fixed_code"):
                continue
            
            # 3. 保存经验（如果修复成功）
            if self.registry:
                self.registry.save_fix(error, fix["fixed_code"])
            
            # 4. 重试执行
            from modules.self_evolution.skill_executor import SkillExecutor
            executor = SkillExecutor(self.registry)
            result = executor.execute(fix["fixed_code"], skill_id)
            
            if result.get("success"):
                return {"healed": True, "fixed_code": fix["fixed_code"],
                        "message": f"LLM修复成功", "retries": self._retry_count}
            
            # 更新错误信息继续循环
            error = result.get("error", error)
        
        return {"healed": False, "message": f"自动修复失败（已尝试{self.MAX_RETRIES}次），需要人工介入",
                "retries": self._retry_count}

    def _try_fix(self, code: str, skill_id: int) -> dict:
        """尝试执行修复代码"""
        from modules.self_evolution.skill_executor import SkillExecutor
        executor = SkillExecutor(self.registry)
        return executor.execute(code, skill_id)

    def _llm_analyze(self, error: str, code: str) -> dict:
        """LLM分析错误并生成修复方案"""
        prompt = f"""以下Python代码执行出错，请分析并修复。

代码:
```python
{code}
```

错误信息:
{error}

请返回JSON格式: {{"analysis":"错误原因分析","fixed_code":"修复后的完整Python代码"}}
仅返回JSON，不要其他文字。"""

        try:
            from modules.astrbot_client import chat
            reply = chat(prompt, session_id="_fix_gen")
            
            json_match = re.search(r'\{.*\}', reply, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"analysis": "分析失败", "fixed_code": ""}
