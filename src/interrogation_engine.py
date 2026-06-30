"""
Interrogation Engine: 结构化拷打引擎

核心设计：
1. 决策树驱动：不是清单式提问，而是基于回答解锁新问题
2. PPT 特化：围绕信息层级、视觉节奏、故事线、数据突出等维度
3. 深度挖掘：通过反问、假设、极端场景迫使澄清真实意图
4. 自动终止：信息饱和或关键决策完备时自动停止
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import json
import re


class InterrogationDimension(Enum):
    """拷打维度"""
    PURPOSE = "purpose"           # 用途与场景
    AUDIENCE = "audience"         # 受众画像
    CORE_MESSAGE = "core_message" # 核心信息
    DATA = "data"                 # 数据与证据
    VISUAL = "visual"             # 视觉约束
    TIME = "time"                 # 时间限制
    COMPETITION = "competition"   # 竞品参照
    RISK = "risk"                 # 风险预判


@dataclass
class InterrogationNode:
    """决策树节点"""
    node_id: str
    dimension: InterrogationDimension
    question: str                    # 问题文本
    question_type: str               # "open" | "choice" | "confirm"
    choices: Optional[List[str]] = None  # 选项（如果是 choice 类型）
    follow_ups: Dict[str, List[str]] = field(default_factory=dict)  # 回答→后续问题映射
    is_critical: bool = False        # 是否关键决策（必须回答）
    extraction_pattern: str = ""     # 从回答中提取关键信息的正则


@dataclass
class InterrogationResult:
    """单次回答结果"""
    node_id: str
    question: str
    answer: str
    extracted_info: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0          # AI 对理解准确度的置信度


@dataclass
class InterrogationSummary:
    """拷打完成后的总结文档"""
    core_message: str = ""           # 一句话核心信息
    audience_persona: str = ""       # 听众画像
    key_data: List[str] = field(default_factory=list)
    visual_reference: str = ""       # 视觉参照
    page_limit: int = 10
    time_limit_minutes: int = 15
    biggest_risk: str = ""
    decision_tree_path: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    assumptions_made: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    full_transcript: List[InterrogationResult] = field(default_factory=list)


class DecisionTree:
    """
    PPT 拷打决策树
    
    设计原则：
    - 每个节点代表一个决策点
    - 回答会解锁后续节点
    - 关键节点（is_critical）必须回答
    - 非关键节点可跳过（信息已足够时）
    """
    
    def __init__(self):
        self.nodes: Dict[str, InterrogationNode] = {}
        self._build_tree()
    
    def _build_tree(self):
        """构建 PPT 特化决策树"""
        
        # === 根节点：用途 ===
        self.nodes["root"] = InterrogationNode(
            node_id="root",
            dimension=InterrogationDimension.PURPOSE,
            question="如果只能用3分钟，你必须让听众记住什么？不要想太久，第一反应最重要。",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        # === 用途分支 ===
        self.nodes["purpose_type"] = InterrogationNode(
            node_id="purpose_type",
            dimension=InterrogationDimension.PURPOSE,
            question="这是哪种类型的展示？",
            question_type="choice",
            choices=["学术答辩", "商业路演", "工作汇报", "课程报告", "产品发布", "其他"],
            follow_ups={
                "学术答辩": ["degree_type"],
                "商业路演": ["funding_stage"],
                "工作汇报": ["report_type"],
                "课程报告": ["course_level"],
            },
            is_critical=True
        )
        
        # 学术答辩分支
        self.nodes["degree_type"] = InterrogationNode(
            node_id="degree_type",
            dimension=InterrogationDimension.PURPOSE,
            question="什么学位？",
            question_type="choice",
            choices=["本科", "硕士", "博士"],
            follow_ups={
                "本科": ["audience_composition"],
                "硕士": ["audience_composition", "innovation_highlight"],
                "博士": ["audience_composition", "theoretical_depth"],
            },
            is_critical=True
        )
        
        self.nodes["innovation_highlight"] = InterrogationNode(
            node_id="innovation_highlight",
            dimension=InterrogationDimension.CORE_MESSAGE,
            question="你的核心创新点是什么？用一句话说，不要技术术语。",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        self.nodes["theoretical_depth"] = InterrogationNode(
            node_id="theoretical_depth",
            dimension=InterrogationDimension.CORE_MESSAGE,
            question="你的理论贡献是什么？解决了什么前人没解决的问题？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        # 商业路演分支
        self.nodes["funding_stage"] = InterrogationNode(
            node_id="funding_stage",
            dimension=InterrogationDimension.PURPOSE,
            question="融资阶段？",
            question_type="choice",
            choices=["种子轮", "A轮", "B轮", "C轮+", "非融资（内部汇报）"],
            follow_ups={
                "种子轮": ["problem_existence"],
                "A轮": ["product_validation"],
                "B轮": ["business_model"],
            },
            is_critical=True
        )
        
        self.nodes["problem_existence"] = InterrogationNode(
            node_id="problem_existence",
            dimension=InterrogationDimension.CORE_MESSAGE,
            question="你要解决的核心问题是什么？为什么现在必须解决？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        self.nodes["product_validation"] = InterrogationNode(
            node_id="product_validation",
            dimension=InterrogationDimension.DATA,
            question="有什么数据证明产品有效？（用户数、留存率、收入等）",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(\d+[^，。]*?)"
        )
        
        # === 受众分支 ===
        self.nodes["audience_composition"] = InterrogationNode(
            node_id="audience_composition",
            dimension=InterrogationDimension.AUDIENCE,
            question="听众中一定有一个人会反对你或质疑你，他会是谁？他会怎么质疑？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        self.nodes["audience_expertise"] = InterrogationNode(
            node_id="audience_expertise",
            dimension=InterrogationDimension.AUDIENCE,
            question="听众对这个领域了解多少？",
            question_type="choice",
            choices=[
                "领域专家（不需要背景介绍）",
                "相关专业（需要少量背景）",
                "外行（需要大量铺垫）",
                "混合（有专家也有外行）"
            ],
            is_critical=True
        )
        
        # === 核心信息分支 ===
        self.nodes["core_message_priority"] = InterrogationNode(
            node_id="core_message_priority",
            dimension=InterrogationDimension.CORE_MESSAGE,
            question="如果删掉80%的内容，只保留20%，你会保留哪部分？为什么？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        self.nodes["story_line"] = InterrogationNode(
            node_id="story_line",
            dimension=InterrogationDimension.CORE_MESSAGE,
            question="你的故事线是什么？用'从...到...'的句式描述。",
            question_type="open",
            is_critical=False,
            extraction_pattern=r"从(.+)到(.+)"
        )
        
        # === 数据分支 ===
        self.nodes["key_metrics"] = InterrogationNode(
            node_id="key_metrics",
            dimension=InterrogationDimension.DATA,
            question="哪个数字如果放大到全屏，最能说服人？为什么是这个数字？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(\d+\.?\d*)\s*(%|倍|x|ms|fps|GB|MB|个|项)"
        )
        
        self.nodes["data_visualization"] = InterrogationNode(
            node_id="data_visualization",
            dimension=InterrogationDimension.DATA,
            question="你有什么图表或图片素材？",
            question_type="open",
            is_critical=False,
            extraction_pattern=r"(.+)"
        )
        
        # === 视觉分支 ===
        self.nodes["visual_preference"] = InterrogationNode(
            node_id="visual_preference",
            dimension=InterrogationDimension.VISUAL,
            question="你有没有见过一个PPT，觉得'这就是我想要的'？描述一下。",
            question_type="open",
            is_critical=False,
            extraction_pattern=r"(.+)"
        )
        
        self.nodes["brand_constraints"] = InterrogationNode(
            node_id="brand_constraints",
            dimension=InterrogationDimension.VISUAL,
            question="有品牌色、学校VI、或机构Logo必须使用吗？",
            question_type="choice",
            choices=["有品牌色/VI", "有Logo需展示", "两者都有", "都没有（自由设计）"],
            is_critical=True
        )
        
        # === 时间分支 ===
        self.nodes["time_limit"] = InterrogationNode(
            node_id="time_limit",
            dimension=InterrogationDimension.TIME,
            question="总共多少时间？每页你打算讲多久？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(\d+)\s*分钟"
        )
        
        self.nodes["page_limit"] = InterrogationNode(
            node_id="page_limit",
            dimension=InterrogationDimension.TIME,
            question="有页数限制吗？",
            question_type="open",
            is_critical=False,
            extraction_pattern=r"(\d+)\s*页"
        )
        
        # === 风险分支 ===
        self.nodes["biggest_risk"] = InterrogationNode(
            node_id="biggest_risk",
            dimension=InterrogationDimension.RISK,
            question="如果展示结束后，听众说'这个工作/产品没什么特别的'，你会怎么反驳？",
            question_type="open",
            is_critical=True,
            extraction_pattern=r"(.+)"
        )
        
        self.nodes["backup_plan"] = InterrogationNode(
            node_id="backup_plan",
            dimension=InterrogationDimension.RISK,
            question="如果技术部分讲不清楚，你有没有一个'一句话总结'能救场？",
            question_type="open",
            is_critical=False,
            extraction_pattern=r"(.+)"
        )
    
    def get_next_nodes(self, current_node_id: str, answer: str) -> List[str]:
        """根据当前节点和回答，获取下一个节点"""
        node = self.nodes.get(current_node_id)
        if not node:
            return []
        
        # 如果有 follow_ups，根据回答匹配
        if node.follow_ups:
            for pattern, next_ids in node.follow_ups.items():
                if pattern in answer:
                    return next_ids
        
        # 默认：按维度顺序推进
        dimension_order = [
            InterrogationDimension.PURPOSE,
            InterrogationDimension.AUDIENCE,
            InterrogationDimension.CORE_MESSAGE,
            InterrogationDimension.DATA,
            InterrogationDimension.VISUAL,
            InterrogationDimension.TIME,
            InterrogationDimension.RISK,
        ]
        
        current_idx = dimension_order.index(node.dimension)
        if current_idx < len(dimension_order) - 1:
            next_dim = dimension_order[current_idx + 1]
            # 返回该维度的第一个节点
            for nid, n in self.nodes.items():
                if n.dimension == next_dim and nid != current_node_id:
                    return [nid]
        
        return []
    
    def extract_info(self, node_id: str, answer: str) -> Dict[str, Any]:
        """从回答中提取结构化信息"""
        node = self.nodes.get(node_id)
        if not node or not node.extraction_pattern:
            return {"raw_answer": answer}
        
        match = re.search(node.extraction_pattern, answer)
        if match:
            return {"extracted": match.group(1), "raw_answer": answer}
        
        return {"raw_answer": answer}


class InterrogationEngine:
    """
    拷打引擎主类
    
    使用示例：
        engine = InterrogationEngine()
        engine.start_interrogation()
        
        while not engine.is_complete():
            question = engine.get_next_question()
            print(question)
            answer = input("用户回答: ")
            engine.record_answer(question, answer)
        
        summary = engine.generate_summary()
        print(summary.core_message)
    """
    
    def __init__(self, memory_context: Optional[Dict] = None):
        self.tree = DecisionTree()
        self.memory = memory_context or {}
        self.results: List[InterrogationResult] = []
        self.visited_nodes: set = set()
        self.pending_nodes: List[str] = ["root"]
        self.critical_decisions: Dict[str, Any] = {}
        self.information_saturation_count: int = 0
        self.last_extracted_info: Dict[str, Any] = {}
    
    def start_interrogation(self):
        """开始拷打会话"""
        # 如果有记忆，先加载偏好
        if self.memory.get("user_profile"):
            profile = self.memory["user_profile"]
            print(f"[记忆加载] 检测到您的偏好: {profile.get('design_dna', {})}")
        
        return self.get_next_question()
    
    def get_next_question(self) -> Optional[InterrogationNode]:
        """获取下一个问题"""
        if not self.pending_nodes:
            return None
        
        node_id = self.pending_nodes.pop(0)
        self.visited_nodes.add(node_id)
        
        node = self.tree.nodes.get(node_id)
        return node
    
    def record_answer(self, node_id: str, answer: str):
        """记录用户回答"""
        node = self.tree.nodes.get(node_id)
        if not node:
            return
        
        # 提取信息
        extracted = self.tree.extract_info(node_id, answer)
        
        # 检测信息饱和度
        if self._is_information_new(extracted):
            self.information_saturation_count = 0
        else:
            self.information_saturation_count += 1
        
        self.last_extracted_info = extracted
        
        # 记录结果
        result = InterrogationResult(
            node_id=node_id,
            question=node.question,
            answer=answer,
            extracted_info=extracted,
            confidence=self._calculate_confidence(answer, extracted)
        )
        self.results.append(result)
        
        # 如果是关键决策，记录
        if node.is_critical:
            self.critical_decisions[node.dimension.value] = extracted
        
        # 获取后续节点
        next_nodes = self.tree.get_next_nodes(node_id, answer)
        for nid in next_nodes:
            if nid not in self.visited_nodes:
                self.pending_nodes.append(nid)
    
    def is_complete(self) -> bool:
        """检查拷打是否完成"""
        # 终止条件 1：信息饱和
        if self.information_saturation_count >= 3:
            return True
        
        # 终止条件 2：关键决策完备
        critical_dimensions = [
            InterrogationDimension.PURPOSE,
            InterrogationDimension.AUDIENCE,
            InterrogationDimension.CORE_MESSAGE,
            InterrogationDimension.DATA,
            InterrogationDimension.VISUAL,
            InterrogationDimension.TIME,
            InterrogationDimension.RISK,
        ]
        completed = sum(1 for d in critical_dimensions 
                       if d.value in self.critical_decisions)
        if completed >= 5:  # 至少5个关键维度有答案
            return True
        
        # 终止条件 3：没有更多问题
        if not self.pending_nodes:
            return True
        
        return False
    
    def generate_summary(self) -> InterrogationSummary:
        """生成拷打总结"""
        summary = InterrogationSummary()
        
        # 提取核心信息
        for result in self.results:
            if result.node_id == "root":
                summary.core_message = result.extracted_info.get("extracted", result.answer)
            elif result.node_id == "audience_composition":
                summary.audience_persona = result.answer
            elif result.node_id == "key_metrics":
                summary.key_data.append(result.extracted_info.get("extracted", ""))
            elif result.node_id == "visual_preference":
                summary.visual_reference = result.answer
            elif result.node_id == "time_limit":
                time_match = re.search(r"(\d+)", result.answer)
                if time_match:
                    summary.time_limit_minutes = int(time_match.group(1))
            elif result.node_id == "page_limit":
                page_match = re.search(r"(\d+)", result.answer)
                if page_match:
                    summary.page_limit = int(page_match.group(1))
            elif result.node_id == "biggest_risk":
                summary.biggest_risk = result.answer
        
        # 决策树路径
        summary.decision_tree_path = list(self.visited_nodes)
        
        # 计算置信度
        summary.confidence_score = self._calculate_overall_confidence()
        
        # 记录未解决问题
        summary.unresolved_questions = self._identify_unresolved()
        
        # 记录假设
        summary.assumptions_made = self._identify_assumptions()
        
        # 完整记录
        summary.full_transcript = self.results
        
        return summary
    
    def _is_information_new(self, extracted: Dict) -> bool:
        """检查提取的信息是否是新的"""
        if not extracted or not self.last_extracted_info:
            return True
        return extracted != self.last_extracted_info
    
    def _calculate_confidence(self, answer: str, extracted: Dict) -> float:
        """计算对回答理解的置信度"""
        confidence = 1.0
        
        # 如果回答太短，置信度降低
        if len(answer) < 5:
            confidence *= 0.5
        
        # 如果回答太模糊，置信度降低
        vague_words = ["随便", "都可以", "你定", "差不多", "还行"]
        if any(w in answer for w in vague_words):
            confidence *= 0.3
        
        # 如果没有提取到有效信息，置信度降低
        if not extracted.get("extracted"):
            confidence *= 0.7
        
        return confidence
    
    def _calculate_overall_confidence(self) -> float:
        """计算整体置信度"""
        if not self.results:
            return 0.0
        
        avg_confidence = sum(r.confidence for r in self.results) / len(self.results)
        
        # 关键决策完备度加权
        critical_count = len([r for r in self.results 
                            if self.tree.nodes.get(r.node_id, InterrogationNode("", InterrogationDimension.PURPOSE, "", "")).is_critical])
        completeness = min(critical_count / 7, 1.0)  # 7个关键维度
        
        return avg_confidence * 0.6 + completeness * 0.4
    
    def _identify_unresolved(self) -> List[str]:
        """识别未解决的问题"""
        unresolved = []
        
        # 检查是否有视觉约束但未明确
        has_visual = any(r.node_id == "visual_preference" for r in self.results)
        if not has_visual:
            unresolved.append("用户未明确视觉偏好，可能需要默认设计")
        
        # 检查是否有页数限制但未明确
        has_page_limit = any(r.node_id == "page_limit" for r in self.results)
        if not has_page_limit:
            unresolved.append("页数限制未明确，将基于时间自动估算")
        
        return unresolved
    
    def _identify_assumptions(self) -> List[str]:
        """识别 AI 做出的假设"""
        assumptions = []
        
        # 从 self.results 提取关键信息
        time_limit = 0
        page_limit = 0
        visual_reference = ""
        for r in self.results:
            if r.node_id == "time_limit":
                m = re.search(r"(\d+)", r.answer)
                if m:
                    time_limit = int(m.group(1))
            elif r.node_id == "page_limit":
                m = re.search(r"(\d+)", r.answer)
                if m:
                    page_limit = int(m.group(1))
            elif r.node_id == "visual_preference":
                visual_reference = r.answer
        
        # 假设 1：时间分配
        if time_limit > 0 and page_limit == 0:
            estimated_pages = time_limit // 2  # 假设每页2分钟
            assumptions.append(f"未明确页数限制，假设 {estimated_pages} 页（每页约2分钟）")
        
        # 假设 2：视觉风格
        if not visual_reference:
            assumptions.append("未明确视觉参照，将基于用途和受众自动设计")
        
        return assumptions


# ═══════════════════════════════════════════
# 与 LLM 的集成接口
# ═══════════════════════════════════════════

def generate_interrogation_prompt(memory_context: Optional[Dict] = None) -> str:
    """
    生成拷打引擎的 LLM prompt
    
    这个 prompt 指导 LLM 如何拷打用户，不是简单的问答，
    而是结构化挖掘。
    """
    
    memory_section = ""
    if memory_context and memory_context.get("user_profile"):
        profile = memory_context["user_profile"]
        memory_section = f"""
## 用户历史偏好（从记忆中加载）
- 常用主题: {profile.get('design_dna', {}).get('preferred_themes', [])}
- 色温偏好: {profile.get('design_dna', {}).get('color_temperature', '未知')}
- 布局偏好: {profile.get('design_dna', {}).get('layout_biases', [])}
- 行业: {profile.get('content_patterns', {}).get('industries', [])}

基于以上偏好，拷打时可以跳过已知的部分，聚焦于不确定的维度。
"""
    
    prompt = f"""# PPT 需求拷打专家

你是一个专业的 PPT 内容策划师。你的任务不是直接做 PPT，而是通过结构化拷打，帮助用户发现他们真正需要的是什么。

## 核心原则

1. **不要接受模糊答案**：如果用户说"随便"、"你定"，继续追问，直到获得具体信息
2. **用极端场景测试**："如果时间只有一半，你会砍掉哪部分？"
3. **挖掘隐性需求**：用户没说的往往比说的更重要
4. **PPT 特化思维**：每个问题都要思考"这如何影响最终的视觉呈现"

## 拷打维度（按优先级）

### 维度 1: 核心信息（最高优先级）
- "如果只能用3分钟，你必须让听众记住什么？"
- "如果删掉80%的内容，保留哪20%？"
- "你的故事线是什么？用'从...到...'描述"

### 维度 2: 受众画像
- "听众中谁会反对你？他会怎么质疑？"
- "听众对这个领域了解多少？"
- "他们最关心什么？最不在乎什么？"

### 维度 3: 数据与证据
- "哪个数字放大到全屏最能说服人？"
- "有什么图表或图片素材？"
- "数据有什么限制或 caveat？"

### 维度 4: 视觉约束
- "你见过哪个 PPT 觉得'这就是我想要的'？"
- "有品牌色、Logo 或 VI 必须使用吗？"
- "对颜色、风格有什么禁忌吗？"

### 维度 5: 时间与节奏
- "总共多少时间？每页讲多久？"
- "有没有必须重点讲的页？"
- "是否有提问环节？"

### 维度 6: 风险与防御
- "如果听众说'没什么特别的'，你怎么反驳？"
- "最可能被质疑的点是什么？"
- "有没有 backup plan？"

{memory_section}

## 拷打终止条件

满足任一即停止：
1. 连续3轮没有获得新的有效信息
2. 以下6个核心决策都有明确答案：核心信息、受众、关键数据、视觉基调、时间、风险
3. 用户明确说"够了，开始做吧"

## 输出格式

拷打完成后，输出 JSON：

```json
{{
  "core_message": "一句话核心信息",
  "audience_persona": "听众画像",
  "key_data": ["关键数据1", "关键数据2"],
  "visual_reference": "视觉参照描述",
  "time_limit": 15,
  "page_limit": 10,
  "biggest_risk": "最大风险场景",
  "unresolved": ["未明确的问题"],
  "assumptions": ["AI 做出的假设"]
}}
```

现在开始拷打。
"""
    
    return prompt


# 注：原模块级 `run_interrogation` 函数（mock 实现）已删除。
# 真实拷打流程请使用：
#   1. PPTOrchestrator.start_interrogation(user_input) → 启动并返回第一个问题 prompt
#   2. PPTOrchestrator.advance_interrogation(ctx, answer) → 推进决策树
#   3. PPTOrchestrator.force_complete_interrogation(ctx) → 强制结束生成 summary
# 旧 API 已不兼容。
