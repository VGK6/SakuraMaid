"""
自我进化系统 — 主入口，整合所有模块
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

class SelfEvolution:
    """自我进化系统主接口"""

    def __init__(self):
        from modules.self_evolution.skill_registry import SkillRegistry
        from modules.self_evolution.skill_generator import SkillGenerator
        from modules.self_evolution.skill_executor import SkillExecutor
        from modules.self_evolution.error_healer import ErrorHealer
        
        self.registry = SkillRegistry()
        self.generator = SkillGenerator(self.registry)
        self.executor = SkillExecutor(self.registry)
        self.healer = ErrorHealer(self.registry)

    def process(self, task: str) -> dict:
        """
        处理用户指令：匹配→生成→执行→诊疗
        返回: {"action": "chat"|"execute"|"confirm"|"error", ...}
        """
        # 1. 查原子技能
        from modules.self_evolution.atomic_skills import match as atomic_match
        atomic = atomic_match(task)
        if atomic:
            result = self.executor.execute(atomic["code"])
            return self._wrap("execute", atomic["name"], result)

        # 2. 查注册技能
        skill = self.registry.match(task)
        if skill:
            # 环境指纹检查
            current_fp = self.registry.get_fingerprint()
            if skill.get("env_fingerprint") and skill["env_fingerprint"] != current_fp:
                return self._wrap("confirm", skill["name"], 
                                  {"message": f"环境已变更，是否尝试迁移？"})
            
            result = self.executor.execute(skill["code"], skill["id"])
            
            # 执行失败 → 错误诊疗
            if not result.get("success"):
                heal = self.healer.heal(result.get("error", ""), skill["code"], skill["id"])
                if heal.get("healed"):
                    result = self.executor.execute(heal["fixed_code"], skill["id"])
                    return self._wrap("execute", skill["name"], result, heal["message"])
                return self._wrap("error", skill["name"], result, heal["message"])
            
            return self._wrap("execute", skill["name"], result)

        # 3. 无匹配 → LLM生成
        gen = self.generator.confirm_and_register(task)
        
        if gen.get("action") == "confirm":
            return self._wrap("confirm", "", {}, gen.get("message", "需要确认"))
        
        if gen.get("action") == "registered":
            skill = gen["skill"]
            result = self.executor.execute(skill["code"])
            return self._wrap("execute", skill["name"], result, f"新技能已注册")
        
        if gen.get("action") == "conflict":
            return self._wrap("confirm", "", {}, gen.get("message", "技能冲突"))
        
        return self._wrap("error", "", {}, gen.get("message", "无法处理"))

    def _wrap(self, action: str, name: str, result: dict, message: str = "") -> dict:
        return {
            "action": action,        # chat/execute/confirm/error
            "skill_name": name,
            "success": result.get("success", False),
            "output": result.get("output", ""),
            "error": result.get("error", ""),
            "message": message or result.get("output", result.get("error", "")),
        }
