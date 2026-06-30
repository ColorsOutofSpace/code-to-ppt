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
from design_contract import DesignContract, ThemeType
from layout_manager import LayoutManager, LayoutType


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
        self.design_contract: Optional[DesignContract] = None  # 由 start_session 按 deck_type 初始化
        self.layout_manager: Optional[LayoutManager] = None     # 由 start_session 初始化
    
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
        
        # 初始化设计契约（按 deck_type 选主题）
        theme = self._infer_theme_from_deck_type(deck_type)
        self.design_contract = DesignContract(theme)
        
        # 初始化布局管理器
        self.layout_manager = LayoutManager()
        
        print(f"[会话启动] {self.session.session_id} - {topic}")
        print(f"[设计主题] {theme.value}")
        
        # 注入记忆上下文
        memory_context = self.memory.generate_context_injection(deck_type=deck_type)
        print(f"[记忆注入]\n{memory_context}")
        
        return self.session
    
    def _infer_theme_from_deck_type(self, deck_type: str) -> ThemeType:
        """根据 deck_type 推断主题"""
        mapping = {
            "thesis": ThemeType.ACADEMIC,
            "academic": ThemeType.ACADEMIC,
            "research": ThemeType.ACADEMIC,
            "pitch": ThemeType.BUSINESS,
            "business": ThemeType.BUSINESS,
            "report": ThemeType.BUSINESS,
            "medical": ThemeType.MEDICAL,
            "healthcare": ThemeType.MEDICAL,
            "tech": ThemeType.TECH,
            "technology": ThemeType.TECH,
            "creative": ThemeType.CREATIVE,
            "design": ThemeType.CREATIVE,
        }
        return mapping.get(deck_type.lower(), ThemeType.ACADEMIC)
    
    def end_session(self, outcome: str = "success", user_feedback: str = "") -> Dict:
        """
        结束会话并返回 Post-Session Reflection 的 prompt 包。
        
        LLM 工具应在 end_session 后：
        1. 读 result['reflection_prompt'] 获得复盘系统指令
        2. 自行分析本次会话（基于 execution_log + corrections_made 等）
        3. 调用 apply_post_session_reflection(report) 把新错误/洞察写入记忆
        """
        if not self.session:
            return {"action": "no_session"}
        
        self.session.status = "completed"
        
        # 保存会话记录
        self.memory.end_session(self.session.session_id, outcome, user_feedback)
        
        # 生成 Post-Session Reflection prompt 包
        reflection_prompt = self._post_session_reflection()
        
        print(f"[会话结束] {self.session.session_id}")
        print(f"  生成页数: {self.session.slides_generated}")
        print(f"  遇到错误: {self.session.errors_encountered}")
        print(f"  修正次数: {self.session.corrections_made}")
        print(f"  [提示] LLM 工具请调用 apply_post_session_reflection() 完成记忆更新")
        
        return {
            "action": "session_ended",
            "session_id": self.session.session_id,
            "stats": {
                "slides_generated": self.session.slides_generated,
                "errors_encountered": self.session.errors_encountered,
                "corrections_made": self.session.corrections_made,
            },
            "outcome": outcome,
            "reflection_prompt": reflection_prompt,
        }
    
    # ═══════════════════════════════════════════
    # 拷打阶段
    # ═══════════════════════════════════════════
    
    def start_interrogation(self, user_input: str = "") -> Dict:
        """
        启动拷打会话：初始化决策树并返回第一个问题 prompt 包。
        
        LLM 工具调用本方法后：
        1. 读 ctx['prompt_for_llm'] 获得拷打系统指令
        2. 读 ctx['current_node'] 获得当前节点（问题、选项、follow_ups）
        3. 自行向用户提问，记录回答
        4. 调用 advance_interrogation(ctx, answer) 推进决策树
        5. 重复 2-4 直到 ctx['status'] == "completed"，从 ctx['summary'] 读取结果
        """
        self.session.current_phase = "interrogating"
        
        # 初始化拷打引擎（带记忆上下文）
        memory_context = {
            "user_profile": self.memory.bundle.user_profile.to_dict() if self.memory.bundle else {}
        }
        self.interrogation_engine = InterrogationEngine(memory_context)
        self._interrogation_answers: List[Tuple[str, str]] = []  # (node_id, answer)
        
        # 启动决策树
        first_node = self.interrogation_engine.start_interrogation()
        
        # 注入记忆上下文
        memory_injection = self.memory.generate_context_injection(current_phase="interrogation")
        
        # 生成拷打系统 prompt（给 LLM 工具的完整指令）
        from interrogation_engine import generate_interrogation_prompt
        system_prompt = generate_interrogation_prompt(memory_context)
        
        print(f"[拷打开始] 基于用户输入: {user_input[:50]}...")
        print(f"[拷打起始节点] {first_node.node_id}: {first_node.question[:50]}...")
        
        return {
            "status": "in_progress",
            "initial_input": user_input,
            "current_node": {
                "node_id": first_node.node_id,
                "dimension": first_node.dimension.value,
                "question": first_node.question,
                "question_type": first_node.question_type,
                "choices": first_node.choices,
                "is_critical": first_node.is_critical,
            },
            "system_prompt": system_prompt,
            "memory_context": memory_injection,
            "extracted_so_far": {},
            "transcript": [],
            "summary": None,
        }
    
    def advance_interrogation(self, ctx: Dict, answer: str) -> Dict:
        """
        推进拷打决策树：处理用户回答，返回下一个问题 prompt 或最终 summary。
        
        Args:
            ctx: start_interrogation() 返回的上下文
            answer: 用户对当前问题的回答
        
        Returns:
            新的 ctx：
            - status="in_progress" 时：current_node 是下一个问题
            - status="completed" 时：summary 字段包含 InterrogationSummary
            - status="needs_user_fatigue_check" 时：表示信息饱和，让 LLM 询问用户是否继续
        """
        if not self.interrogation_engine or ctx.get("status") != "in_progress":
            return ctx
        
        current_node_id = ctx["current_node"]["node_id"]
        
        # 记录回答
        self.interrogation_engine.record_answer(current_node_id, answer)
        self._interrogation_answers.append((current_node_id, answer))
        ctx["transcript"].append({
            "node_id": current_node_id,
            "question": ctx["current_node"]["question"],
            "answer": answer,
        })
        
        # 检测用户疲劳（连续 3 轮无新信息）
        if self.interrogation_engine.information_saturation_count >= 3:
            print(f"[拷打告警] 连续 3 轮无新信息，建议询问用户是否继续")
            ctx["status"] = "needs_user_fatigue_check"
            return ctx
        
        # 获取下一个问题
        next_node = self.interrogation_engine.get_next_question()
        
        if next_node is None:
            # 决策树走完，生成 summary
            summary = self.interrogation_engine.generate_summary()
            self.session.interrogation_summary = summary.__dict__
            ctx["summary"] = summary  # InterrogationSummary 实例
            ctx["summary_dict"] = summary.__dict__  # dict 副本（供 LLM 工具查看）
            ctx["status"] = "completed"
            ctx["current_node"] = None
            print(f"[拷打完成] 置信度: {summary.confidence_score}")
            return ctx
        
        ctx["current_node"] = {
            "node_id": next_node.node_id,
            "dimension": next_node.dimension.value,
            "question": next_node.question,
            "question_type": next_node.question_type,
            "choices": next_node.choices,
            "is_critical": next_node.is_critical,
        }
        return ctx
    
    def force_complete_interrogation(self, ctx: Dict) -> Dict:
        """
        强制结束拷打（用户主动停止 / LLM 判断关键决策已完备）。
        基于已收集的回答生成 summary，不要求走完整棵决策树。
        """
        if not self.interrogation_engine:
            ctx["status"] = "error"
            ctx["error"] = "拷打引擎未初始化"
            return ctx
        
        summary = self.interrogation_engine.generate_summary()
        self.session.interrogation_summary = summary.__dict__
        ctx["summary"] = summary  # InterrogationSummary 实例（供 generate_plan 使用）
        ctx["summary_dict"] = summary.__dict__  # dict 副本（供 LLM 工具查看）
        ctx["status"] = "completed"
        ctx["current_node"] = None
        print(f"[拷打强制结束] 已收集 {len(self._interrogation_answers)} 个回答")
        return ctx
    
    def run_interrogation(self, user_input: str = "") -> InterrogationSummary:
        """
        【保留以兼容旧 API】一次性拷打（不推荐使用）。
        
        推荐工作流：start_interrogation() → 多次 advance_interrogation() → force_complete_interrogation()
        本方法保留是因为旧文档/示例可能引用，但实际效果有限——只触发决策树第一个问题。
        """
        ctx = self.start_interrogation(user_input)
        # 提示用户推荐新 API
        print("[DEPRECATED] run_interrogation() 已弃用，推荐用 start_interrogation() + advance_interrogation()")
        # 兼容性 fallback：直接返回部分填空的 summary
        summary = InterrogationSummary()
        summary.core_message = user_input
        summary.confidence_score = 0.3
        self.session.interrogation_summary = summary.__dict__
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
                              review_type: str = "plan") -> Dict:
        """
        准备对抗审查的 LLM prompt 包。
        
        返回给 LLM 工具的不是审查结果，而是三 Agent 的独立 prompt：
        - agents[0]: Creative（视觉/创新）
        - agents[1]: Logic（论证/连贯）
        - agents[2]: Execution（资源/风险）
        
        LLM 工具应：
        1. 分别以三个 Agent 视角独立审查 content
        2. 各自输出 ReviewReport JSON（带 score / findings）
        3. 调用 aggregate_review(reports) 汇总为 AdversarialReviewResult
        """
        print(f"[对抗审查] 类型: {review_type} (返回 prompt 包，让 LLM 工具执行三个 Agent)")
        return self.adversarial_engine.build_review_prompts(content, review_type)
    
    def aggregate_review(self, reports: List[Dict]) -> AdversarialReviewResult:
        """
        LLM 工具执行 run_adversarial_review 后，把三个 Agent 的输出（list of ReviewReport dict）传回，
        本方法负责聚合为 AdversarialReviewResult（计算总分、判断通过、生成 action items）。
        """
        result = self.adversarial_engine.aggregate_findings(reports)
        print(f"[审查聚合] 综合评分: {result.overall_score:.1f}/10")
        print(f"[审查聚合] 是否通过: {'是' if result.is_passed else '否'}")
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
        为单页生成准备完整的 LLM prompt 包。
        
        返回的不是"已生成的结果"，而是给 LLM 工具的完整指令：
        - system_prompt: 设计契约、反 AI 味规则、SKILL.md 工作流摘要
        - user_prompt: 当前页的具体内容（标题/布局/bullets）
        - design_contract: 完整色板/字体/节奏状态
        - memory_context: 用户偏好 + 已知错误警示
        - validation_warnings: Python 端 DesignContract 验证发现的违规
        
        LLM 工具读 prompt 后，按 SKILL.md Phase 4 的工作流：
        1. 计算垂直空间预算
        2. 估算文本行数
        3. 反推 cd() 高度
        4. 写完整 python-pptx 代码
        5. 执行代码生成 .pptx
        """
        self.session.current_phase = "executing"
        
        if self.design_contract is None:
            self.design_contract = DesignContract(ThemeType.ACADEMIC)
        
        # Python 端做设计契约验证（这部分是真实的规则检查）
        is_valid, validation_errors = self.design_contract.validate_before_build(slide_config)
        
        # 注入记忆上下文
        memory_injection = self.memory.generate_context_injection(current_phase="slide_generation")
        
        slide_num = slide_config.get("slide_number", "?")
        layout = slide_config.get("layout", "content_single")
        title = slide_config.get("title", "")
        content = slide_config.get("content", "")
        key_metrics = slide_config.get("key_metrics", [])
        
        # 构造 system_prompt：设计契约 + 反 AI 味规则
        contract = self.design_contract
        system_prompt = f"""你是 PPT 制作专家。基于以下设计约束，为第 {slide_num} 页生成完整可执行的 python-pptx 代码。

═══════════════════════════════════
设计契约（DesignContract）
═══════════════════════════════════
- 主题: {contract.theme.value}
- 主色: {contract.color_palette.primary}
- 辅色: {contract.color_palette.secondary}
- 中性色: {contract.color_palette.neutral}
- 语义色: positive={contract.get_color('positive')}, warning={contract.get_color('warning')}, contrast={contract.get_color('contrast')}
- 字体: 中文={contract.typography.chinese}, 英文={contract.typography.english}
- 字号: 标题={contract.typography.title_size}pt, 正文={contract.typography.body_size}pt, hero={contract.typography.hero_size}pt
- 行距: {contract.typography.line_spacing}

═══════════════════════════════════
反 AI 味规则（必须严格遵守）
═══════════════════════════════════
- 无左侧竖线装饰（这是 AI 生成 PPT 最常见的视觉指纹）
- 无 box shadow / 投影
- 至少 3 种不同布局混用
- 关键指标用 hero() 突出（{contract.typography.hero_size}pt）
- 页脚是短线（~1.8"），不是全宽线
- 强调线颜色语义化（positive=绿, warning=红, contrast=金）
- 数据要具体（不要定性描述，要有数字）
- 无 clipart 图标，只用几何形状
- 每页最多 8 行 bullet
- 正文字号 ≥ {contract.ANTI_AI_RULES['min_body_font_size']}pt

═══════════════════════════════════
布局计算步骤（参考 SKILL.md Phase 4.2）
═══════════════════════════════════
1. 垂直空间预算：列出所有元素 y/h，总和 ≤ 4.3"
2. 文本实际行数估算：每行容纳中文字数 = (w - 0.28) / 0.132
3. cd() 高度反推：h_card = 0.42 + 行数 × fs × ls / 72 + 0.05
4. 剩余空间分配

═══════════════════════════════════
Helper 函数（参考 reference.md 第 1 节）
═══════════════════════════════════
- cd(sl, l, t, w, h, title, body, accent): 内容卡片
- plot_card(sl, l, t, w, h, name, title, accent): 图片卡片
- hero(sl, l, t, w, h, number, label, accent): 大字统计
- band(sl, l, t, w, h, color): 色带
- ft(sl, n): 页脚
- st(sl, title) / sT(sl, title, sub): 章节标签 / 主标题
- img_fit(sl, name, l, t, max_w, max_h, align): 等比缩放图片

═══════════════════════════════════
输出要求
═══════════════════════════════════
输出完整可执行的 python-pptx 代码块，包含：
- 必要 import
- 色板常量（PRIMARY, SECONDARY, NEUTRAL, SEMANTIC_POSITIVE 等）
- 16:9 画布初始化
- 当前页的完整代码
- prs.save(output_path)
"""
        
        # 构造 user_prompt：当前页具体内容
        user_prompt = f"""请为第 {slide_num} 页生成代码：

布局: {layout}
标题: {title}
内容: {content if content else '(参见下方 bullets)'}
关键指标: {key_metrics if key_metrics else '无'}

输出格式：完整 python-pptx 代码块（用 ```python ... ``` 包裹）。"""
        
        if not is_valid and validation_errors:
            user_prompt += "\n\n⚠️ 设计契约验证警告（必须修正）：\n" + "\n".join(f"  - {e}" for e in validation_errors)
        
        # 记录到执行日志
        result = {
            "action": "generate_python_pptx_code",
            "slide_number": slide_num,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "design_contract": {
                "theme": contract.theme.value,
                "color_palette": contract.color_palette.to_dict(),
                "typography": contract.typography.to_dict(),
            },
            "memory_context": memory_injection,
            "validation_warnings": validation_errors,
            "expected_output": "完整可执行的 python-pptx 代码（```python ... ```）",
        }
        
        self.session.slides_generated += 1
        self.session.execution_log.append(result)
        
        return result
    
    # ═══════════════════════════════════════════
    # 反思阶段
    # ═══════════════════════════════════════════
    
    def reflect_on_slide(self, slide_result: Dict) -> Dict:
        """
        为 Per-Slide 反思准备 LLM prompt 包。
        
        返回的是给 LLM 工具的检查指令：
        - system_prompt: 反思原则 + 已知错误模式
        - checklist: 8 项必查项目
        - known_errors: 从 Error Registry 匹配到的相关错误
        - slide_png: 可选，提供生成的页面 PNG 供视觉审查
        
        LLM 工具读 prompt 后：
        1. 逐项检查 checklist
        2. 对比 known_errors
        3. 输出 reflection_report（findings 列表）
        4. 调用 correct_slide() 修正（如有 findings）
        """
        # 加载已知错误模式（从记忆系统）
        relevant_errors = self.memory.get_relevant_errors(context="slide_generation")
        known_errors_data = [
            {
                "error_type": e.error_type,
                "description": e.description,
                "root_cause": e.root_cause,
                "prevention": e.prevention,
            }
            for e in relevant_errors
        ]
        
        # 反 AI 味 checklist（来自 DesignContract）
        anti_ai_rules = self.design_contract.ANTI_AI_RULES if self.design_contract else {}
        
        system_prompt = f"""你是 PPT 质量审查员。对第 {slide_result.get('slide_number', '?')} 页做 Per-Slide 反思。

═══════════════════════════════════
反思原则
═══════════════════════════════════
- 不只检查语法错误，更要检查"AI 味"和一致性
- 文字溢出、图片变形、元素重叠是高频问题
- 检查与 DesignContract 的一致性（色板、字体、节奏）
- 反思结果驱动修正，不是装饰

═══════════════════════════════════
Checklist（每页必查）
═══════════════════════════════════
内容检查：
1. 是否超过 {anti_ai_rules.get('max_bullets_per_slide', 8)} 行 bullet？
2. 是否有具体数据（非纯定性描述）？
3. 核心信息是否在一句话内可概括？

视觉检查（反 AI 味）：
4. 布局是否与 DesignContract 的 visual_reference 一致？
5. 强调线颜色是否语义化（positive/warning/contrast）？
6. 是否存在左侧竖线装饰（禁止）？
7. 页脚是否为短线（~1.8"，不是全宽）？
8. 是否使用了 clipart 图标（禁止，只用几何形状）？

一致性检查：
9. 与前页的过渡是否自然？
10. 字体、字号是否遵循 DesignContract？
11. 颜色是否与色板一致？

节奏检查：
12. 是否已连续 2 页同布局？（如果是，告警）
13. 距上次 hero_panel 是否 ≥2 页？（如果不足，告警）

═══════════════════════════════════
已知错误模式（避免重复）
═══════════════════════════════════
"""
        if known_errors_data:
            for err in known_errors_data:
                system_prompt += f"⚠️ [{err['error_type']}] {err['description']}\n   根因: {err['root_cause']}\n   预防: {err['prevention']}\n\n"
        else:
            system_prompt += "（暂无相关错误记录）\n"
        
        system_prompt += """
═══════════════════════════════════
输出格式
═══════════════════════════════════
按 checklist 逐项输出 findings 列表：
```json
{
  "slide_number": N,
  "needs_correction": true/false,
  "findings": [
    {
      "check_id": 6,
      "severity": "high|medium|low",
      "issue": "...",
      "suggestion": "..."
    }
  ]
}
```
"""
        
        return {
            "action": "check_slide",
            "slide_number": slide_result.get("slide_number"),
            "system_prompt": system_prompt,
            "checklist": [
                f"内容: bullet ≤ {anti_ai_rules.get('max_bullets_per_slide', 8)} 行、有具体数据、核心信息一句话可概括",
                "视觉: 强调线语义化、无左侧竖线、页脚短线、无 clipart",
                "一致性: 字体字号遵循 DesignContract、颜色与色板一致",
                "节奏: 避免连续同布局、hero 间距 ≥2 页",
            ],
            "known_errors": known_errors_data,
            "expected_output": "reflection_report JSON",
        }
    
    def correct_slide(self, slide_result: Dict, reflection: Dict) -> Dict:
        """
        为修正幻灯片准备 LLM prompt 包。
        
        Args:
            slide_result: execute_slide() 返回的 prompt 包
            reflection: LLM 工具执行 reflect_on_slide 后给出的 findings
        
        Returns:
            修正 prompt：让 LLM 重新生成受影响的页面
        """
        self.session.corrections_made += 1
        slide_num = slide_result.get("slide_number", "?")
        findings = reflection.get("findings", [])
        
        if not findings:
            return {
                "action": "no_correction_needed",
                "slide_number": slide_num,
                "message": "无 findings，无需修正",
            }
        
        # 按 severity 排序
        high_priority = [f for f in findings if f.get("severity") == "high"]
        medium_priority = [f for f in findings if f.get("severity") == "medium"]
        low_priority = [f for f in findings if f.get("severity") == "low"]
        
        system_prompt = f"""你是 PPT 修正专家。第 {slide_num} 页有 {len(findings)} 个问题需要修正。

═══════════════════════════════════
修正原则
═══════════════════════════════════
- 高优先级问题必须修正
- 中优先级问题尽量修正
- 低优先级问题可选择性修正（如不影响阅读）
- 修正时保持原有设计意图，不要改标题和核心内容
- 修正后必须重新通过 Per-Slide 反思

═══════════════════════════════════
需要修正的问题
═══════════════════════════════════
"""
        for i, f in enumerate(high_priority + medium_priority + low_priority, 1):
            severity_label = {"high": "🔴 高", "medium": "🟡 中", "low": "🟢 低"}.get(f.get("severity", "low"), "⚪")
            system_prompt += f"{i}. {severity_label} {f.get('issue', '')}\n   建议: {f.get('suggestion', '')}\n\n"
        
        system_prompt += f"""
═══════════════════════════════════
原页信息
═══════════════════════════════════
- 布局: {slide_result.get('design_contract', {}).get('theme', '?')}
- 设计契约: 主题={slide_result.get('design_contract', {}).get('theme')}

═══════════════════════════════════
输出
═══════════════════════════════════
完整可执行的 python-pptx 代码块（修正后版本）。
"""
        
        return {
            "action": "regenerate_slide",
            "slide_number": slide_num,
            "system_prompt": system_prompt,
            "findings": findings,
            "high_priority_count": len(high_priority),
            "expected_output": "修正后的 python-pptx 代码块",
        }
    
    def _post_session_reflection(self) -> Dict:
        """
        会话结束后的反思 prompt 包，让 LLM 总结本次会话并提取新的错误/洞察。
        """
        if not self.session:
            return {"action": "no_session"}
        
        # 统计本次会话
        slide_count = self.session.slides_generated
        correction_count = self.session.corrections_made
        error_count = self.session.errors_encountered
        
        # 收集本次会话用过的所有布局（从 memory）
        layouts_used = []
        if self.session.execution_log:
            for entry in self.session.execution_log[-10:]:
                if "design_contract" in entry:
                    layouts_used.append(entry.get("design_contract", {}).get("theme", "?"))
        
        system_prompt = f"""你是 PPT 项目复盘专家。本次会话已结束，需要生成复盘报告并更新记忆。

═══════════════════════════════════
本次会话统计
═══════════════════════════════════
- 生成页数: {slide_count}
- 修正次数: {correction_count}
- 错误次数: {error_count}
- 使用的主题: {set(layouts_used) if layouts_used else '未记录'}

═══════════════════════════════════
复盘维度
═══════════════════════════════════
1. 哪些设计选择效果好？（值得记录为 Insight）
2. 哪些错误/问题反复出现？（值得记录为 Error）
3. 用户的偏好是否需要在 User Profile 中更新？
4. 下次类似场景可以怎么改进？

═══════════════════════════════════
输出格式
═══════════════════════════════════
```json
{{
  "summary": "本次会话一句话总结",
  "new_errors": [
    {{
      "error_type": "...",
      "description": "...",
      "root_cause": "...",
      "prevention": "..."
    }}
  ],
  "new_insights": [
    {{
      "insight": "...",
      "trigger": "...",
      "application_scope": "...",
      "confidence": 0.0-1.0
    }}
  ],
  "profile_updates": {{
    "design_dna_changes": {{}},
    "communication_style_changes": {{}}
  }}
}}
```

LLM 工具应将以上 JSON 传给 orchestrator.apply_post_session_reflection() 来更新记忆。
"""
        
        return {
            "action": "post_session_reflection",
            "session_id": self.session.session_id,
            "system_prompt": system_prompt,
            "stats": {
                "slides_generated": slide_count,
                "corrections_made": correction_count,
                "errors_encountered": error_count,
            },
            "expected_output": "复盘 JSON 报告",
        }
    
    def apply_post_session_reflection(self, report: Dict):
        """
        LLM 工具执行 _post_session_reflection 后，把复盘报告传回来，
        本方法负责把新错误/洞察/用户偏好更新到 MemoryManager。
        """
        if not self.session:
            return
        
        # 记录新错误
        for err in report.get("new_errors", []):
            self.memory.record_error(
                error_type=err.get("error_type", "unknown"),
                description=err.get("description", ""),
                root_cause=err.get("root_cause", ""),
                prevention=err.get("prevention", ""),
                session_id=self.session.session_id,
            )
            self.session.errors_encountered += 1
        
        # 记录新洞察
        for ins in report.get("new_insights", []):
            self.memory.record_insight(
                insight=ins.get("insight", ""),
                trigger=ins.get("trigger", ""),
                application_scope=ins.get("application_scope", "general"),
                session_id=self.session.session_id,
            )
        
        # 更新用户偏好
        profile_updates = report.get("profile_updates", {})
        for category, changes in profile_updates.items():
            if changes and self.memory.bundle:
                # 这里需要 MemoryManager 提供 update_profile 方法
                if hasattr(self.memory, 'update_user_preference'):
                    self.memory.update_user_preference(category, changes)
        
        print(f"[Post-Session Reflection 完成] 新错误: {len(report.get('new_errors', []))}, 新洞察: {len(report.get('new_insights', []))}")
    
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
