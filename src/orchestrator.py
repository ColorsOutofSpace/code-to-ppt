"""
Orchestrator: 主控制器

职责：
1. 协调拷打引擎、计划管理、记忆系统、即时反思、对抗审查
2. 管理会话生命周期（启动→拷打→计划→执行→反思→交付）
3. 处理用户命令（/interrogate, /plan, /memory, /reflect, /review）
4. 与执行层对接输入输出
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from interrogation_engine import InterrogationEngine, InterrogationSummary
from memory_system import MemoryManager, get_memory_manager
from adversarial_review import AdversarialReviewEngine, AdversarialReviewResult


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: str
    start_time: str
    status: str = "active"  # active/paused/completed
    
    # 当前状态
    current_phase: str = "idle"  # idle/interrogating/planning/executing/reflecting
    interrogation_summary: Optional[Dict] = None
    plan_document: Optional[Dict] = None
    execution_log: List[Dict] = field(default_factory=list)
    
    # 统计
    slides_generated: int = 0
    errors_encountered: int = 0
    corrections_made: int = 0


class PPTOrchestrator:
    """
    PPT 制作 Orchestrator
    
    使用示例：
        orch = PPTOrchestrator(user_id="user_123")
        
        # 启动会话
        orch.start_session("基于深度学习的医学影像分析")
        
        # 拷打
        summary = orch.run_interrogation()
        
        # 生成计划
        plan = orch.generate_plan(summary)
        
        # 对抗审查（计划审查）
        review = orch.run_adversarial_review(plan, "plan")
        if not review.is_passed:
            orch.modify_plan(review.action_items)
        
        # 执行生成（调用执行层）
        for slide_config in plan["slides"]:
            result = orch.execute_slide(slide_config)
            
            # Per-Slide 反思
            reflection = orch.reflect_on_slide(result)
            if reflection["needs_correction"]:
                orch.correct_slide(result, reflection)
            
            # Checkpoint 审查（每3页）
            if orch.session.slides_generated % 3 == 0:
                checkpoint_review = orch.run_adversarial_review(
                    orch.get_recent_slides(3), "checkpoint"
                )
        
        # 最终审查
        final_review = orch.run_adversarial_review(orch.get_full_deck(), "final")
        
        # 结束会话
        orch.end_session()
    """
    
    def __init__(self, user_id: str = "anonymous"):
        self.user_id = user_id
        self.memory = get_memory_manager(user_id)
        self.session: Optional[SessionContext] = None
        self.interrogation_engine: Optional[InterrogationEngine] = None
        self.adversarial_engine = AdversarialReviewEngine()
    
    # ═══════════════════════════════════════════
    # 会话生命周期管理
    # ═══════════════════════════════════════════
    
    def start_session(self, topic: str, deck_type: str = "general") -> SessionContext:
        """启动新会话"""
        self.session = SessionContext(
            session_id=f"ses_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=self.user_id,
            start_time=datetime.now().isoformat(),
        )
        
        # 记录到记忆系统
        self.memory.start_session(self.session.session_id, topic, deck_type)
        
        print(f"[会话启动] {self.session.session_id} - {topic}")
        
        # 注入记忆上下文
        memory_context = self.memory.generate_context_injection(deck_type=deck_type)
        print(f"[记忆注入]\n{memory_context}")
        
        return self.session
    
    def end_session(self, outcome: str = "success", user_feedback: str = ""):
        """结束会话"""
        if not self.session:
            return
        
        self.session.status = "completed"
        
        # 保存会话记录
        self.memory.end_session(self.session.session_id, outcome, user_feedback)
        
        # 运行 Post-Session Reflection
        self._post_session_reflection()
        
        print(f"[会话结束] {self.session.session_id}")
        print(f"  生成页数: {self.session.slides_generated}")
        print(f"  遇到错误: {self.session.errors_encountered}")
        print(f"  修正次数: {self.session.corrections_made}")
    
    # ═══════════════════════════════════════════
    # 拷打阶段
    # ═══════════════════════════════════════════
    
    def run_interrogation(self, user_input: str = "") -> InterrogationSummary:
        """
        运行拷打流程
        
        实际实现中，这里会：
        1. 生成拷打 prompt（注入记忆上下文）
        2. 调用 LLM 进行多轮对话
        3. 解析输出为结构化结果
        """
        self.session.current_phase = "interrogating"
        
        # 初始化拷打引擎
        memory_context = {
            "user_profile": self.memory.bundle.user_profile.to_dict() if self.memory.bundle else {}
        }
        self.interrogation_engine = InterrogationEngine(memory_context)
        
        # 生成拷打 prompt
        from interrogation_engine import generate_interrogation_prompt
        prompt = generate_interrogation_prompt(memory_context)
        
        print(f"[拷打开始] 基于用户输入: {user_input[:50]}...")
        print(f"[拷打 Prompt 长度] {len(prompt)} 字符")
        
        # 在实际实现中，这里会将 prompt 和对话历史传给 LLM
        # 简化版：返回模拟结果
        summary = InterrogationSummary()
        summary.core_message = user_input
        summary.confidence_score = 0.7
        
        self.session.interrogation_summary = summary.__dict__
        
        print(f"[拷打完成] 置信度: {summary.confidence_score}")
        
        return summary
    
    # ═══════════════════════════════════════════
    # 计划阶段
    # ═══════════════════════════════════════════
    
    def generate_plan(self, interrogation_summary: InterrogationSummary) -> Dict:
        """
        基于拷打结果生成计划
        
        实际实现中，这里会：
        1. 调用 Plan Manager 生成结构化计划
        2. 注入用户偏好和过往洞察
        3. 向用户展示计划，获得确认
        """
        self.session.current_phase = "planning"
        
        # 基于拷打结果推断计划参数
        estimated_pages = interrogation_summary.page_limit
        if estimated_pages == 0 and interrogation_summary.time_limit_minutes > 0:
            estimated_pages = interrogation_summary.time_limit_minutes // 2
        
        plan = {
            "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "version": 1,
            "status": "draft",
            "estimated_pages": estimated_pages,
            "estimated_duration_minutes": interrogation_summary.time_limit_minutes,
            "phases": [
                {
                    "phase_id": "p1",
                    "phase_name": "视觉设计",
                    "status": "pending",
                    "tasks": [
                        {
                            "task_id": "p1-t1",
                            "task_name": "确定四层色板",
                            "status": "pending",
                            "checkpoint": "向用户展示色板，获得确认"
                        },
                        {
                            "task_id": "p1-t2", 
                            "task_name": "确定字体层级",
                            "status": "pending",
                            "checkpoint": "与色板一起展示"
                        }
                    ]
                },
                {
                    "phase_id": "p2",
                    "phase_name": "内容架构",
                    "status": "pending",
                    "tasks": [
                        {
                            "task_id": "p2-t1",
                            "task_name": "设计故事线",
                            "status": "pending",
                            "checkpoint": "向用户展示故事线大纲"
                        }
                    ]
                },
                {
                    "phase_id": "p3",
                    "phase_name": "页面生成",
                    "status": "pending",
                    "tasks": []  # 动态生成
                }
            ],
            "slides": []
        }
        
        # 基于拷打结果生成幻灯片大纲
        # 在实际实现中，这里会调用 slide_mapper
        plan["slides"] = self._generate_slide_outline(interrogation_summary)
        
        self.session.plan_document = plan
        
        print(f"[计划生成] 预计 {plan['estimated_pages']} 页")
        
        return plan
    
    def _generate_slide_outline(self, summary: InterrogationSummary) -> List[Dict]:
        """基于拷打结果生成幻灯片大纲"""
        slides = []
        
        # 封面
        slides.append({
            "slide_number": 1,
            "slide_type": "cover",
            "layout": "cover",
            "title": summary.core_message[:30] if summary.core_message else "封面",
            "status": "planned"
        })
        
        # 目录（如果页数>5）
        if summary.page_limit > 5:
            slides.append({
                "slide_number": 2,
                "slide_type": "outline",
                "layout": "outline",
                "title": "汇报提纲",
                "status": "planned"
            })
        
        # 内容页（简化版）
        for i in range(3, min(summary.page_limit, 10)):
            slides.append({
                "slide_number": i,
                "slide_type": "content",
                "layout": "content_single",
                "title": f"第{i-2}部分",
                "status": "planned"
            })
        
        # 致谢
        slides.append({
            "slide_number": len(slides) + 1,
            "slide_type": "thankyou",
            "layout": "cover",
            "title": "谢谢",
            "status": "planned"
        })
        
        return slides
    
    def modify_plan(self, action_items: List[Dict]):
        """根据审查意见修改计划"""
        if not self.session or not self.session.plan_document:
            return
        
        for item in action_items:
            if item["priority"] == "立即执行":
                print(f"[计划修改] {item['action']}")
                # 实际实现中，这里会修改 plan_document
                self.session.plan_document["version"] += 1
    
    # ═══════════════════════════════════════════
    # 对抗审查
    # ═══════════════════════════════════════════
    
    def run_adversarial_review(self, content: Dict, 
                              review_type: str = "plan") -> AdversarialReviewResult:
        """运行对抗审查"""
        print(f"[对抗审查] 类型: {review_type}")
        
        result = self.adversarial_engine.review_plan(content)
        
        if review_type == "checkpoint":
            result = self.adversarial_engine.review_checkpoint(content)
        elif review_type == "final":
            result = self.adversarial_engine.review_final(content)
        
        print(f"[审查结果] 综合评分: {result.overall_score:.1f}/10")
        print(f"[审查结果] 是否通过: {'是' if result.is_passed else '否'}")
        
        if result.action_items:
            print(f"[行动项] 共 {len(result.action_items)} 项")
            for item in result.action_items[:3]:
                print(f"  - [{item['priority']}] {item['action']}")
        
        return result
    
    # ═══════════════════════════════════════════
    # 执行阶段（与执行层对接）
    # ═══════════════════════════════════════════
    
    def execute_slide(self, slide_config: Dict) -> Dict:
        """
        执行单页生成
        
        实际实现中，这里会调用执行层的生成逻辑
        """
        self.session.current_phase = "executing"
        
        # 注入记忆上下文
        memory_context = self.memory.generate_context_injection(
            current_phase="slide_generation"
        )
        
        # 调用执行层生成
        # 简化版：模拟生成
        result = {
            "slide_number": slide_config["slide_number"],
            "status": "generated",
            "memory_injected": len(memory_context) > 0,
        }
        
        self.session.slides_generated += 1
        self.session.execution_log.append(result)
        
        return result
    
    # ═══════════════════════════════════════════
    # 反思阶段
    # ═══════════════════════════════════════════
    
    def reflect_on_slide(self, slide_result: Dict) -> Dict:
        """
        Per-Slide 反思
        
        运行检查清单，发现问题则返回修正建议
        """
        reflection = {
            "slide_number": slide_result.get("slide_number"),
            "needs_correction": False,
            "findings": [],
        }
        
        # 检查 1：是否触发已知错误模式
        relevant_errors = self.memory.get_relevant_errors(context="slide_generation")
        if relevant_errors:
            reflection["findings"].append({
                "type": "error_pattern",
                "message": f"注意: 有 {len(relevant_errors)} 个过往错误模式需要避免"
            })
        
        # 检查 2：是否符合用户偏好
        # 简化版：假设通过
        
        return reflection
    
    def correct_slide(self, slide_result: Dict, reflection: Dict):
        """根据反思结果修正幻灯片"""
        self.session.corrections_made += 1
        print(f"[自动修正] 第 {slide_result['slide_number']} 页")
        # 实际实现中，这里会修改幻灯片
    
    def _post_session_reflection(self):
        """Post-Session 反思"""
        if not self.session:
            return
        
        print("[Post-Session Reflection]")
        
        # 记录新错误
        if self.session.errors_encountered > 0:
            self.memory.record_error(
                error_type="session_errors",
                description=f"本次会话遇到 {self.session.errors_encountered} 个错误",
                root_cause="待分析",
                prevention="加强 Per-Slide 检查",
                session_id=self.session.session_id
            )
        
        # 记录新洞察
        if self.session.corrections_made > 0:
            self.memory.record_insight(
                insight=f"本次会话进行了 {self.session.corrections_made} 次自动修正",
                trigger="Post-Session 反思",
                application_scope="general",
                session_id=self.session.session_id
            )
        
        print(f"  错误记录: {self.session.errors_encountered}")
        print(f"  洞察记录: {self.session.corrections_made}")
    
    # ═══════════════════════════════════════════
    # 用户命令处理
    # ═══════════════════════════════════════════
    
    def handle_command(self, command: str, args: Dict = None) -> str:
        """处理用户命令"""
        args = args or {}
        
        if command == "/interrogate":
            return "开始拷打流程..."
        
        elif command == "/plan":
            if self.session and self.session.plan_document:
                return json.dumps(self.session.plan_document, ensure_ascii=False, indent=2)
            return "暂无计划，请先运行拷打"
        
        elif command == "/memory":
            return self.memory.generate_user_summary()
        
        elif command == "/reflect":
            if self.session:
                reflection = self.reflect_on_slide({"slide_number": self.session.slides_generated})
                return json.dumps(reflection, ensure_ascii=False, indent=2)
            return "暂无会话"
        
        elif command == "/review":
            if self.session and self.session.plan_document:
                result = self.run_adversarial_review(self.session.plan_document, "plan")
                return self.adversarial_engine.generate_review_report(result)
            return "暂无计划可审查"
        
        elif command == "/save-memory":
            self.memory.save()
            return "记忆已保存"
        
        else:
            return f"未知命令: {command}"
    
    # ═══════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════
    
    def get_recent_slides(self, count: int = 3) -> List[Dict]:
        """获取最近生成的页面"""
        if not self.session:
            return []
        return self.session.execution_log[-count:]
    
    def get_full_deck(self) -> Dict:
        """获取完整 deck 信息"""
        if not self.session:
            return {}
        return {
            "session": self.session.__dict__,
            "plan": self.session.plan_document,
            "execution_log": self.session.execution_log,
        }


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def create_orchestrator(user_id: str = "anonymous") -> PPTOrchestrator:
    """创建 Orchestrator 实例"""
    return PPTOrchestrator(user_id)


# 示例用法
if __name__ == "__main__":
    # 创建 orchestrator
    orch = create_orchestrator(user_id="demo_user")
    
    # 启动会话
    orch.start_session("基于深度学习的医学影像分析", deck_type="thesis")
    
    # 拷打
    summary = orch.run_interrogation("我要做一个硕士答辩PPT，关于医学影像分割")
    
    # 生成计划
    plan = orch.generate_plan(summary)
    
    # 计划审查
    review = orch.run_adversarial_review(plan, "plan")
    
    # 执行一页
    if plan["slides"]:
        result = orch.execute_slide(plan["slides"][0])
        reflection = orch.reflect_on_slide(result)
    
    # 结束会话
    orch.end_session(outcome="success", user_feedback="整体满意")
