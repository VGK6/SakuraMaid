"""
LLM技能生成器 — 遇到新任务时生成Python技能
"""
import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

class SkillGenerator:
    """用LLM生成新技能"""

    def __init__(self, registry=None):
        self.registry = registry

    def generate(self, task: str) -> dict:
        """生成技能: 原子匹配→LLM生成→安全检查→用户确认"""
        # 1. 先查原子技能
        from modules.self_evolution.atomic_skills import match as atomic_match
        atomic = atomic_match(task)
        if atomic:
            return {"source": "atomic", "skill": atomic}

        # 2. 查注册表
        if self.registry:
            existing = self.registry.match(task)
            if existing:
                return {"source": "registry", "skill": existing}

        # 3. LLM生成(仅当无匹配时)
        return self._llm_generate(task)

    def _llm_generate(self, task: str) -> dict:
        """调用LLM生成技能代码"""
        prompt = f"""你是一个Python代码生成助手。用户需要完成以下任务：
"{task}"

请生成一个Python脚本来完成这个任务。
要求：
- 只能在 ~/Desktop, ~/Downloads, ~/Documents 目录下操作文件
- 禁止使用 os.remove, shutil.rmtree, subprocess, eval, exec 等危险操作
- 代码要简短高效，直接输出结果
- 返回JSON格式: {{"name":"技能名","keywords":["触发词1","触发词2"],"code":"Python代码","description":"功能描述"}}
- 仅返回JSON，不要其他文字"""

        try:
            from modules.astrbot_client import chat
            reply = chat(prompt, session_id="_skill_gen")
            
            # 提取JSON
            json_match = re.search(r'\{.*\}', reply, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # 安全检查
                risks = self._scan_code(result.get("code", ""))
                result["risks"] = risks
                return {"source": "llm", "skill": result}
        except Exception as e:
            return {"source": "error", "error": str(e)}
        
        return {"source": "error", "error": "LLM未返回有效结果"}

    def _scan_code(self, code: str) -> list:
        """简单安全检查"""
        risks = []
        dangerous = [
            (r'os\.remove|os\.unlink|shutil\.rmtree', '文件删除操作'),
            (r'subprocess\.|os\.system', '系统命令执行'),
            (r'eval\(|exec\(|__import__', '动态代码执行'),
        ]
        for pattern, desc in dangerous:
            if re.search(pattern, code):
                risks.append(desc)
        return risks

    def confirm_and_register(self, task: str, user_accepted: bool = False) -> dict:
        """生成→确认→注册"""
        result = self.generate(task)
        
        if result.get("source") == "atomic":
            return {"action": "execute", "skill": result["skill"], "message": f"原子技能: {result['skill']['name']}"}
        
        if result.get("source") == "registry":
            return {"action": "execute", "skill": result["skill"], "message": f"已有技能: {result['skill']['name']}"}
        
        if result.get("source") == "llm":
            skill = result.get("skill", {})
            risks = skill.get("risks", [])
            
            if risks and not user_accepted:
                return {"action": "confirm", "skill": skill, "risks": risks,
                        "message": f"检测到风险: {', '.join(risks)}，是否继续？"}
            
            # 注册技能
            if self.registry and skill.get("name") and skill.get("keywords"):
                reg_result = self.registry.register(
                    skill["name"], skill["keywords"], skill.get("code", ""), 50
                )
                if reg_result.get("conflict"):
                    return {"action": "conflict", "skill": skill, **reg_result}
                return {"action": "registered", "skill": skill, "message": f"已注册: {skill['name']}"}
        
        return {"action": "error", "message": result.get("error", "生成失败")}
