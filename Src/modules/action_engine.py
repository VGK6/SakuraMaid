"""
动作引擎 — 桌宠的"大脑"
观察屏幕 → LLM分析 → 自动生成动作 → 执行
"""
import json, time, base64, os, tempfile
from io import BytesIO

class ActionEngine:
    """动作引擎：理解环境→决策→执行→反馈循环"""

    def __init__(self):
        self.virtual_hand = None
        self.screen = None
        self._init_modules()

    def _init_modules(self):
        """延迟导入避免循环依赖"""
        try:
            from modules.virtual_hand import VirtualHand
            from modules.screen_capture import ScreenCapture
            self.virtual_hand = VirtualHand()
            self.screen = ScreenCapture()
        except Exception as e:
            print(f"动作引擎初始化失败: {e}")

    def execute(self, task: str) -> dict:
        """
        执行用户任务的主入口
        流程: 截图 → llva分析 → LLM决策 → 执行 → 反馈
        """
        if not self.virtual_hand or not self.screen:
            return {"success": False, "error": "模块未初始化"}

        # 第一步: 截图到资源目录temp
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "resourses", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        screenshot_path = os.path.join(temp_dir, "screen_shot.png")
        self.screen.save_screenshot(screenshot_path)
        
        win_info = self.screen.get_active_window_info()
        
        # 第二步: 用llava详细分析屏幕内容
        screen_desc = self._describe_screen(screenshot_path)

        # 第三步: 让LLM决策（包含屏幕描述）
        plan = self._plan_actions(task, screen_desc, win_info)

        # 清理截图
        try:
            os.remove(screenshot_path)
        except:
            pass

        if not plan.get("actions"):
            return {"success": False, "error": plan.get("error", "LLM无法生成动作计划")}

        # 第四步: 执行动作序列
        results = self._execute_plan(plan["actions"])

        success = all(r.get("success") for r in results)

        return {
            "success": success,
            "plan": plan["actions"],
            "results": results,
            "summary": plan.get("reasoning", ""),
        }

    def _describe_screen(self, screenshot_path: str) -> str:
        """用llava分析屏幕内容"""
        try:
            from modules.vision import describe_image
            result = describe_image(screenshot_path)
            if result and not result.startswith("llava调用失败"):
                return result
        except:
            pass
        # 回退：简单描述
        try:
            from PIL import Image
            img = Image.open(screenshot_path)
            win = self.screen.get_active_window_info()
            color = self.screen.get_foreground_color()
            return f"屏幕 {img.size[0]}x{img.size[1]}, {color}色调, 当前窗口: {win['title']}"
        except:
            return "无法分析屏幕"

    def _plan_actions(self, task: str, screen_desc: str, win_info: dict) -> dict:
        """
        使用LLM规划动作序列
        返回格式: {"actions": [...], "reasoning": "..."}
        """
        prompt = f"""你是一个桌面助手，需要根据用户指令和当前屏幕状态，生成具体的操作步骤。

当前屏幕: {screen_desc}
活动窗口: {win_info.get('title', '未知')}

用户指令: {task}

请返回JSON格式的操作计划，包含：
1. reasoning: 你的分析思路
2. actions: 操作步骤数组，每步格式:
   {{"type": "click"|"type"|"hotkey"|"scroll"|"wait"|"analyze",
    "params": {{...}},
    "description": "这一步做什么"}}

支持的action类型:
- click(x, y): 在屏幕坐标点击
- click(text): 点击包含某文字的区域(需结合截图分析)
- type(text): 输入文字
- hotkey(keys): 快捷键,如 ["ctrl", "c"]
- scroll(direction, amount): 滚动
- wait(ms): 等待毫秒
- analyze(question): 分析当前屏幕再回答
- screenshot(): 截图保存

仅返回JSON，不要其他文字。"""

        try:
            # 通过AstrBot API调用LLM
            from modules.astrbot_client import chat
            reply = chat(prompt, session_id="_action_plan")

            # 尝试解析JSON
            if reply:
                # 提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', reply, re.DOTALL)
                if json_match:
                    plan = json.loads(json_match.group())
                    return plan
            return {"actions": [], "error": "LLM响应格式错误"}
        except Exception as e:
            return {"actions": [], "error": str(e)}

    def _execute_plan(self, actions: list) -> list:
        """执行动作序列"""
        results = []
        for i, action in enumerate(actions):
            try:
                result = self._execute_one(action)
                results.append({"step": i, **result})
                time.sleep(0.3)  # 动作间隙
            except Exception as e:
                results.append({"step": i, "success": False, "error": str(e)})
                break  # 失败就停止
        return results

    def _execute_one(self, action: dict) -> dict:
        """执行单个动作"""
        atype = action.get("type", "")
        params = action.get("params", {})

        if atype == "click":
            x, y = params.get("x", 0), params.get("y", 0)
            btn = params.get("button", "left")
            self.virtual_hand.click(x, y, button=btn)
            return {"success": True, "message": f"点击 ({x},{y})"}

        elif atype == "type":
            text = params.get("text", "")
            self.virtual_hand.type_text(text)
            return {"success": True, "message": f"输入: {text[:20]}..."}

        elif atype == "hotkey":
            keys = params.get("keys", [])
            if isinstance(keys, list):
                self.virtual_hand.hotkey(*keys)
            else:
                self.virtual_hand.hotkey(keys)
            return {"success": True, "message": f"快捷键: {keys}"}

        elif atype == "wait":
            ms = params.get("ms", 1000)
            time.sleep(ms / 1000)
            return {"success": True, "message": f"等待 {ms}ms"}

        elif atype == "scroll":
            direction = params.get("direction", "down")
            amount = params.get("amount", 3)
            self.virtual_hand.scroll(direction, amount)
            return {"success": True, "message": f"滚动 {direction}"}

        elif atype == "screenshot":
            path = self.screen.save_screenshot()
            return {"success": True, "message": f"截图: {path}", "screenshot": path}

        elif atype == "analyze":
            question = params.get("question", "屏幕上有啥？")
            # 用llava分析截图（后续接入）
            return {"success": True, "message": f"分析: {question}"}

        return {"success": False, "error": f"未知动作类型: {atype}"}


    def auto_mode(self, instruction: str):
        """一键执行模式：用户说一句，AI自动完成"""
        result = self.execute(instruction)
        if result["success"]:
            return f"✅ 任务完成! {result['summary']}"
        else:
            return f"❌ 任务失败: {result.get('error', '未知错误')}"
