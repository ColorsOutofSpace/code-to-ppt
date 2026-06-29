"""
Adversarial Review: 多 Agent 独立对抗审查系统

核心设计：
1. 三 Agent 独立审查：Creative（创意）、Logic（逻辑）、Execution（执行）
2. 独立性保证：审查 Agent 不能看到主 Agent 的思考过程，只能看到最终产出
3. 交叉验证：三方意见综合，发现单 Agent 无法发现的盲点
4. 触发时机：计划审查、Checkpoint 审查、最终审查
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json


class ReviewerType(Enum):
    """审查者类型"""
    CREATIVE = "creative"       # 创意审查
    LOGIC = "logic"             # 逻辑审查
    EXECUTION = "execution"     # 执行审查


class ReviewSeverity(Enum):
    """审查发现严重级别"""
    CRITICAL = "critical"       # 必须修复
    HIGH = "high"               # 强烈建议修复
    MEDIUM = "medium"           # 建议修复
    LOW = "low"                 # 可选优化
    INFO = "info"               # 仅供参考


@dataclass
class ReviewFinding:
    """单个审查发现"""
    finding_id: str
    reviewer: ReviewerType
    severity: ReviewSeverity
    category: str              # 发现类别
    issue: str                 # 问题描述
    evidence: str              # 证据/依据
    suggestion: str            # 改进建议
    affected_pages: List[int] = field(default_factory=list)
    confidence: float = 0.8    # 审查者对此发现的置信度


@dataclass
class ReviewReport:
    """单个审查者的报告"""
    reviewer: ReviewerType
    score: float               # 0-10 分
    findings: List[ReviewFinding] = field(default_factory=list)
    summary: str = ""          # 总体评价
    strengths: List[str] = field(default_factory=list)  # 优点


@dataclass
class AdversarialReviewResult:
    """对抗审查综合结果"""
    review_type: str           # "plan" | "checkpoint" | "final"
    reports: List[ReviewReport] = field(default_factory=list)
    consolidated_findings: List[Dict] = field(default_factory=list)
    action_items: List[Dict] = field(default_factory=list)
    overall_score: float = 0.0
    pass_threshold: float = 7.0
    is_passed: bool = False


# ═══════════════════════════════════════════
# 审查 Prompt 模板
# ═══════════════════════════════════════════

CREATIVE_REVIEWER_PROMPT = """# Creative Reviewer（创意审查）

你是一位资深视觉设计师和创意总监。你的任务是审查 PPT 的**视觉呈现和创意表达**。

## 审查维度

### 1. 视觉吸引力
- 这页够吸引人吗？第一眼能看到重点吗？
- 是否有"哇"的瞬间？还是平淡无奇？
- 配色是否平庸？有没有更出彩的方案？

### 2. 信息层级
- 视线流动是否自然？是否引导到正确的重点？
- 字号对比是否足够？标题、正文、注释是否清晰区分？
- 是否使用了视觉锚点（hero 统计、色带、图标）？

### 3. 布局创新
- 布局是否太保守？有没有更有趣的呈现方式？
- 是否混合使用了多种布局？（反 AI 味检查）
- 每页是否有足够的视觉呼吸空间？

### 4. 品牌一致性
- 配色是否符合场景和品牌？
- 字体选择是否恰当？
- 整体风格是否统一？

## 评分标准

- 10分：惊艳，可以上 Behance 首页
- 8-9分：优秀，超出预期
- 6-7分：合格，但有明显优化空间
- 4-5分：平庸，需要大幅修改
- 1-3分：不合格，必须重做

## 输出格式

```json
{{
  "score": 7.5,
  "summary": "总体评价",
  "strengths": ["优点1", "优点2"],
  "findings": [
    {{
      "severity": "high",
      "category": "visual_hierarchy",
      "issue": "第3页重点不突出",
      "evidence": "关键数据被埋在正文中，没有用 hero 面板",
      "suggestion": "将核心数据提取为 hero 统计，放大到 42pt",
      "affected_pages": [3],
      "confidence": 0.9
    }}
  ]
}}
```

**重要**：你只审查**最终产出**，不看生成过程。保持独立判断，不要被其他审查者影响。
"""


LOGIC_REVIEWER_PROMPT = """# Logic Reviewer（逻辑审查）

你是一位逻辑学家和内容策略师。你的任务是审查 PPT 的**信息结构和论证逻辑**。

## 审查维度

### 1. 论证完整性
- 论点→证据→结论的链条是否完整？
- 有没有逻辑跳跃？听众能跟上吗？
- 前提假设是否明确？有没有隐含假设？

### 2. 信息密度
- 每页信息量是否恰当？（太少=浪费，太多= overwhelm）
- bullet points 是否精炼？有没有冗余？
- 数据是否支撑结论？有没有过度解读？

### 3. 故事线连贯性
- 从第一页到最后一页，故事是否连贯？
- 每页之间的过渡是否自然？
- 是否有明确的起承转合？

### 4. 受众适配
- 内容深度是否符合受众水平？
- 技术术语是否过多或过少？
- 背景铺垫是否足够？

## 评分标准

- 10分：论证无懈可击，故事引人入胜
- 8-9分：逻辑清晰，偶有瑕疵
- 6-7分：大体合理，但有明显漏洞
- 4-5分：逻辑混乱，需要重组
- 1-3分：论证崩溃，必须重写

## 输出格式

```json
{{
  "score": 8.0,
  "summary": "总体评价",
  "strengths": ["优点1", "优点2"],
  "findings": [
    {{
      "severity": "medium",
      "category": "narrative_gap",
      "issue": "第5页从方法跳到实验，缺少过渡",
      "evidence": "第4页结尾是'方法细节'，第5页开头是'实验结果'，中间没有'实验设置'",
      "suggestion": "插入一页'实验设置'，说明数据集、评价指标、对比方法",
      "affected_pages": [4, 5],
      "confidence": 0.85
    }}
  ]
}}
```

**重要**：你只审查**最终产出**，不看生成过程。保持独立判断，不要被其他审查者影响。
"""


EXECUTION_REVIEWER_PROMPT = """# Execution Reviewer（执行审查）

你是一位项目经理和技术审核。你的任务是审查 PPT 的**可执行性和交付风险**。

## 审查维度

### 1. 资源可用性
- 所有引用的图片、图表、数据文件是否存在？
- 字体是否在目标设备上可用？
- 外部链接是否有效？

### 2. 技术可行性
- 复杂布局是否在 python-pptx 能力范围内？
- 动画/过渡效果是否能实现？
- 文件大小是否在合理范围？

### 3. 时间可行性
- 计划在给定时间内可完成吗？
- 是否有步骤需要用户配合（如提供素材）？
- 缓冲时间是否充足？

### 4. 交付物检查
- 输出格式是否正确（.pptx）？
- 分辨率是否满足需求（投影/屏幕/打印）？
- 是否有兼容性问题（Mac/Windows、不同 PowerPoint 版本）？

## 评分标准

- 10分：零风险，可直接交付
- 8-9分：低风险，有小问题可快速修复
- 6-7分：中等风险，需要调整计划
- 4-5分：高风险，可能延误或失败
- 1-3分：不可执行，必须重新规划

## 输出格式

```json
{{
  "score": 6.5,
  "summary": "总体评价",
  "strengths": ["优点1", "优点2"],
  "findings": [
    {{
      "severity": "high",
      "category": "missing_asset",
      "issue": "第7页引用的图片 'fig3.png' 不存在",
      "evidence": "素材目录中没有 fig3.png，只有 fig1.png 和 fig2.png",
      "suggestion": "确认图片路径，或生成红色占位符并提醒用户补充",
      "affected_pages": [7],
      "confidence": 1.0
    }}
  ]
}}
```

**重要**：你只审查**最终产出**，不看生成过程。保持独立判断，不要被其他审查者影响。
"""


# ═══════════════════════════════════════════
# 对抗审查引擎
# ═══════════════════════════════════════════

class AdversarialReviewEngine:
    """
    对抗审查引擎
    
    使用示例：
        engine = AdversarialReviewEngine()
        
        # 计划审查
        result = engine.review_plan(plan_document)
        
        # Checkpoint 审查
        result = engine.review_checkpoint(slides_batch)
        
        # 最终审查
        result = engine.review_final(full_deck)
        
        # 处理结果
        if not result.is_passed:
            for item in result.action_items:
                if item["priority"] == "critical":
                    fix_issue(item)
    """
    
    def __init__(self, pass_threshold: float = 7.0):
        self.pass_threshold = pass_threshold
        self.prompts = {
            ReviewerType.CREATIVE: CREATIVE_REVIEWER_PROMPT,
            ReviewerType.LOGIC: LOGIC_REVIEWER_PROMPT,
            ReviewerType.EXECUTION: EXECUTION_REVIEWER_PROMPT,
        }
    
    def review_plan(self, plan_document: Dict) -> AdversarialReviewResult:
        """
        审查计划文档
        
        Args:
            plan_document: 计划管理器生成的计划 JSON
        """
        result = AdversarialReviewResult(review_type="plan")
        
        # 并行调用三个审查 Agent（实际实现中）
        for reviewer_type in ReviewerType:
            report = self._run_reviewer(reviewer_type, plan_document, "plan")
            result.reports.append(report)
        
        # 综合裁决
        self._consolidate(result)
        
        return result
    
    def review_checkpoint(self, slides_batch: List[Dict], 
                         checkpoint_number: int) -> AdversarialReviewResult:
        """
        Checkpoint 审查（每3页）
        
        Args:
            slides_batch: 最近生成的3页
            checkpoint_number: 第几个 checkpoint
        """
        result = AdversarialReviewResult(review_type="checkpoint")
        
        # Checkpoint 审查简化版：只检查一致性、节奏、明显错误
        for reviewer_type in ReviewerType:
            report = self._run_reviewer(reviewer_type, slides_batch, "checkpoint")
            result.reports.append(report)
        
        self._consolidate(result)
        
        return result
    
    def review_final(self, full_deck: Dict) -> AdversarialReviewResult:
        """
        最终审查
        
        Args:
            full_deck: 完整 deck 的所有信息
        """
        result = AdversarialReviewResult(review_type="final")
        
        for reviewer_type in ReviewerType:
            report = self._run_reviewer(reviewer_type, full_deck, "final")
            result.reports.append(report)
        
        self._consolidate(result)
        
        return result
    
    def _run_reviewer(self, reviewer_type: ReviewerType, 
                     content: Dict, review_type: str) -> ReviewReport:
        """
        运行单个审查 Agent
        
        实际实现中，这里会调用 LLM API，传入 prompt 和 content
        """
        prompt = self.prompts[reviewer_type]
        
        # 模拟审查结果（实际应调用 LLM）
        report = ReviewReport(reviewer=reviewer_type)
        
        # 根据审查类型调整评分逻辑
        if review_type == "plan":
            report.score = 7.5
            report.summary = "计划合理，但有几处可优化"
        elif review_type == "checkpoint":
            report.score = 8.0
            report.summary = "Checkpoint 通过，一致性良好"
        else:  # final
            report.score = 7.0
            report.summary = "整体合格，有小问题需修复"
        
        return report
    
    def _consolidate(self, result: AdversarialReviewResult):
        """综合三方意见，生成最终裁决"""
        
        # 计算平均分
        if result.reports:
            result.overall_score = sum(r.score for r in result.reports) / len(result.reports)
        
        # 判断是否通过
        result.is_passed = result.overall_score >= self.pass_threshold
        
        # 合并所有发现，按严重性排序
        all_findings = []
        for report in result.reports:
            for finding in report.findings:
                all_findings.append({
                    "reviewer": finding.reviewer.value,
                    "severity": finding.severity.value,
                    "category": finding.category,
                    "issue": finding.issue,
                    "suggestion": finding.suggestion,
                    "affected_pages": finding.affected_pages,
                    "confidence": finding.confidence,
                })
        
        # 严重性排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_findings.sort(key=lambda f: severity_order.get(f["severity"], 2))
        
        result.consolidated_findings = all_findings
        
        # 生成 action items
        result.action_items = self._generate_action_items(all_findings)
    
    def _generate_action_items(self, findings: List[Dict]) -> List[Dict]:
        """从发现生成可执行的行动项"""
        actions = []
        
        for finding in findings:
            if finding["severity"] in ["critical", "high"]:
                priority = "立即执行"
            elif finding["severity"] == "medium":
                priority = "建议执行"
            else:
                priority = "可选优化"
            
            actions.append({
                "priority": priority,
                "issue": finding["issue"],
                "action": finding["suggestion"],
                "affected_pages": finding["affected_pages"],
                "source": finding["reviewer"],
            })
        
        return actions
    
    def generate_review_report(self, result: AdversarialReviewResult) -> str:
        """生成人类可读的审查报告"""
        lines = [
            f"# 对抗审查报告 ({result.review_type})",
            f"",
            f"**综合评分**: {result.overall_score:.1f}/10 "
            f"({'通过' if result.is_passed else '未通过'}，阈值: {result.pass_threshold})",
            f"",
        ]
        
        # 各审查者评分
        lines.append("## 各维度评分")
        for report in result.reports:
            lines.append(f"- **{report.reviewer.value}**: {report.score}/10 - {report.summary}")
        lines.append("")
        
        # 关键发现
        if result.consolidated_findings:
            lines.append("## 关键发现")
            for finding in result.consolidated_findings[:10]:  # 只显示前10个
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", 
                        "low": "🟢", "info": "⚪"}.get(finding["severity"], "⚪")
                lines.append(f"{emoji} **[{finding['severity'].upper()}]** {finding['issue']}")
                lines.append(f"   建议: {finding['suggestion']}")
                if finding["affected_pages"]:
                    lines.append(f"   影响页: {finding['affected_pages']}")
                lines.append("")
        
        # 行动项
        if result.action_items:
            lines.append("## 行动项")
            for i, item in enumerate(result.action_items[:5], 1):
                lines.append(f"{i}. **[{item['priority']}]** {item['action']}")
                lines.append(f"   (来源: {item['source']}, 页: {item['affected_pages']})")
            lines.append("")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# 与 Orchestrator 的集成
# ═══════════════════════════════════════════

def run_adversarial_review(content: Dict, review_type: str = "plan",
                          pass_threshold: float = 7.0) -> AdversarialReviewResult:
    """
    便捷函数：运行对抗审查
    
    Args:
        content: 待审查内容（计划/页面/完整deck）
        review_type: "plan" | "checkpoint" | "final"
        pass_threshold: 通过阈值
    
    Returns:
        AdversarialReviewResult
    """
    engine = AdversarialReviewEngine(pass_threshold)
    
    if review_type == "plan":
        return engine.review_plan(content)
    elif review_type == "checkpoint":
        return engine.review_checkpoint(content)
    elif review_type == "final":
        return engine.review_final(content)
    else:
        raise ValueError(f"Unknown review_type: {review_type}")
