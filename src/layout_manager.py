"""
LayoutManager: 基于内容特征的自动布局分配引擎

核心设计：
1. 特征提取(FeatureExtractor): 从 SlideContent 中提取结构/语义/数据特征
2. 布局评分(LayoutScorer): 基于特征向量计算每种布局的匹配度
3. 冲突解决(ConflictResolver): 处理多特征触发时的优先级仲裁
4. 节奏控制(RhythmController): 保证全局布局多样性，避免单调
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class LayoutType(Enum):
    """预定义布局类型，对应 SKILL.md 中的 5.3 节"""
    COVER = "cover"
    OUTLINE = "outline"
    SECTION_DIVIDER = "section_divider"
    TWO_COLUMN_COMPARE = "two_column_compare"
    IMAGE_TOP_ANALYSIS = "image_top_analysis"
    IMAGE_LEFT_TEXT_RIGHT = "image_left_text_right"
    THREE_IMAGES = "three_images"
    TIMELINE = "timeline"
    HERO_PANEL = "hero_panel"
    CONTENT_SINGLE = "content_single"  # 单栏内容页
    CONTENT_DUAL = "content_dual"      # 双栏内容页
    SUMMARY = "summary"


@dataclass
class ContentFeatures:
    """单页内容的特征向量"""
    text_length: int = 0                    # 文本总长度（字符）
    bullet_count: int = 0                   # bullet points 数量
    image_count: int = 0                    # 图片数量
    has_comparison_keywords: bool = False   # 含对比关键词（vs/相比/对比）
    has_timeline_keywords: bool = False     # 含时间关键词（步骤/阶段/流程）
    has_causal_keywords: bool = False       # 含因果关键词（因为/导致/因此）
    has_problem_solution: bool = False      # 含问题-解决结构
    key_metrics_count: int = 0              # 关键指标数量（数字+单位）
    max_metric_value: float = 0.0           # 最大指标数值（用于判断hero面板）
    section_transition: bool = False        # 是否为章节过渡页
    is_title_slide: bool = False            # 是否为封面
    is_closing_slide: bool = False          # 是否为总结/致谢
    data_table_count: int = 0               # 数据表格数量
    chart_count: int = 0                    # 图表数量


@dataclass
class LayoutRecommendation:
    """布局推荐结果"""
    layout: LayoutType
    confidence: float                       # 0.0-1.0
    reasoning: str                          # 推荐理由（供LLM审查）
    alternative: Optional[LayoutType] = None # 备选布局
    alt_confidence: float = 0.0


class FeatureExtractor:
    """从文本内容中提取特征向量"""
    
    COMPARISON_PATTERNS = [
        r"vs\.?", r"versus", r"相比", r"对比", r"比较", 
        r"baseline", r"基线", r"已有方法", r"现有方法",
        r"before", r"after", r"改进前", r"改进后"
    ]
    
    TIMELINE_PATTERNS = [
        r"首先|第一步", r"其次|第二步", r"然后|第三步", r"最后|最终",
        r"阶段", r"步骤", r"流程", r"pipeline", r"workflow",
        r"step \d+", r"phase \d+"
    ]
    
    CAUSAL_PATTERNS = [
        r"因为|由于", r"导致|引起", r"因此|所以", r"从而",
        r"原因", r"结果", r"影响"
    ]
    
    PROBLEM_SOLUTION_PATTERNS = [
        r"问题|挑战|局限|不足",
        r"解决方案|本文提出|我们提出|方法",
        r"为了解决|针对.*问题"
    ]
    
    METRIC_PATTERN = re.compile(
        r"(\d+\.?\d*)\s*(%|倍|x|倍提升|准确率|精度|召回率|F1|ms|fps|GB|MB|个|项)"
    )
    
    def extract(self, title: str, bullets: List[str], images: List[str]) -> ContentFeatures:
        """提取内容特征"""
        f = ContentFeatures()
        all_text = title + " " + " ".join(bullets)
        
        # 基础统计
        f.text_length = len(all_text)
        f.bullet_count = len(bullets)
        f.image_count = len(images)
        
        # 关键词检测
        f.has_comparison_keywords = any(
            re.search(p, all_text, re.I) for p in self.COMPARISON_PATTERNS
        )
        f.has_timeline_keywords = any(
            re.search(p, all_text, re.I) for p in self.TIMELINE_PATTERNS
        )
        f.has_causal_keywords = any(
            re.search(p, all_text, re.I) for p in self.CAUSAL_PATTERNS
        )
        f.has_problem_solution = (
            re.search(self.PROBLEM_SOLUTION_PATTERNS[0], all_text, re.I) and
            re.search(self.PROBLEM_SOLUTION_PATTERNS[1], all_text, re.I)
        )
        
        # 关键指标提取
        metrics = self.METRIC_PATTERN.findall(all_text)
        f.key_metrics_count = len(metrics)
        if metrics:
            f.max_metric_value = max(float(m[0]) for m in metrics)
        
        return f


class LayoutScorer:
    """基于特征向量为每种布局计算匹配分数"""
    
    # 布局-特征匹配规则矩阵
    # 每个规则: (feature_name, operator, threshold, weight)
    SCORING_RULES: Dict[LayoutType, List[Tuple[str, str, any, float]]] = {
        LayoutType.TWO_COLUMN_COMPARE: [
            ("has_comparison_keywords", "==", True, 1.0),
            ("has_problem_solution", "==", True, 0.9),
            ("bullet_count", ">=", 4, 0.3),
            ("image_count", "==", 0, 0.2),  # 纯文本对比更常见
        ],
        LayoutType.TIMELINE: [
            ("has_timeline_keywords", "==", True, 1.0),
            ("bullet_count", ">=", 3, 0.5),
            ("bullet_count", "<=", 6, 0.3),  # 时间线不宜太长
        ],
        LayoutType.HERO_PANEL: [
            ("key_metrics_count", ">=", 1, 0.8),
            ("key_metrics_count", ">=", 3, 1.0),
            ("bullet_count", "<=", 4, 0.4),  # hero页文字不宜多
            ("image_count", "==", 0, 0.2),
        ],
        LayoutType.IMAGE_TOP_ANALYSIS: [
            ("image_count", ">=", 1, 1.0),
            ("bullet_count", ">=", 2, 0.5),
            ("has_causal_keywords", "==", True, 0.3),
        ],
        LayoutType.IMAGE_LEFT_TEXT_RIGHT: [
            ("image_count", ">=", 1, 1.0),
            ("bullet_count", ">=", 3, 0.6),
            ("text_length", ">=", 100, 0.3),
        ],
        LayoutType.THREE_IMAGES: [
            ("image_count", ">=", 3, 1.0),
            ("bullet_count", "<=", 3, 0.4),
        ],
        LayoutType.CONTENT_SINGLE: [
            ("bullet_count", ">=", 3, 0.4),
            ("bullet_count", "<=", 8, 0.3),
            ("image_count", "==", 0, 0.2),
        ],
        LayoutType.CONTENT_DUAL: [
            ("bullet_count", ">=", 6, 0.5),
            ("image_count", "==", 0, 0.2),
            ("has_comparison_keywords", "==", False, 0.1),  # 非对比但内容多
        ],
    }
    
    def score(self, features: ContentFeatures, layout: LayoutType) -> float:
        """计算单一布局的匹配分数 (0.0-1.0)"""
        rules = self.SCORING_RULES.get(layout, [])
        if not rules:
            return 0.1  # 未定义规则给予基础分
        
        total_weight = 0.0
        scored_weight = 0.0
        
        for feature_name, op, threshold, weight in rules:
            value = getattr(features, feature_name)
            match = False
            
            if op == "==":
                match = value == threshold
            elif op == ">=":
                match = value >= threshold
            elif op == "<=":
                match = value <= threshold
            elif op == ">":
                match = value > threshold
            elif op == "<":
                match = value < threshold
            
            total_weight += weight
            if match:
                scored_weight += weight
        
        return scored_weight / total_weight if total_weight > 0 else 0.0
    
    def rank(self, features: ContentFeatures) -> List[Tuple[LayoutType, float]]:
        """对所有布局按匹配度排序"""
        scores = []
        for layout in LayoutType:
            if layout in (LayoutType.COVER, LayoutType.OUTLINE, 
                         LayoutType.SECTION_DIVIDER, LayoutType.SUMMARY):
                continue  # 这些由流程控制决定，不由内容特征决定
            score = self.score(features, layout)
            scores.append((layout, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class RhythmController:
    """
    节奏控制器：保证全局布局多样性
    
    核心规则：
    1. 连续同类型布局不超过 2 页
    2. 至少混合使用 3 种不同布局（反 AI 味规则）
    3. 章节过渡页后强制使用内容页（不打断节奏）
    4. hero 面板后避免紧跟另一 hero 面板
    """
    
    MAX_CONSECUTIVE_SAME = 2
    MIN_LAYOUT_VARIETY = 3
    RHYTHM_BREAKERS = [LayoutType.HERO_PANEL, LayoutType.SECTION_DIVIDER]
    
    def __init__(self):
        self.history: List[LayoutType] = []
        self.layout_counts: Dict[LayoutType, int] = {}
    
    def record(self, layout: LayoutType):
        """记录已使用的布局"""
        self.history.append(layout)
        self.layout_counts[layout] = self.layout_counts.get(layout, 0) + 1
    
    def is_allowed(self, layout: LayoutType) -> Tuple[bool, str]:
        """检查布局是否被节奏规则允许"""
        # 规则 1：连续同类型检查
        consecutive = 0
        for prev in reversed(self.history):
            if prev == layout:
                consecutive += 1
            else:
                break
        
        if consecutive >= self.MAX_CONSECUTIVE_SAME:
            return False, f"连续 {self.MAX_CONSECUTIVE_SAME} 页使用 {layout.value}，需要换布局打破单调"
        
        # 规则 2：hero 面板后不接 hero
        if self.history and self.history[-1] in self.RHYTHM_BREAKERS and layout in self.RHYTHM_BREAKERS:
            return False, f"{self.history[-1].value} 后不宜紧跟 {layout.value}"
        
        return True, "通过节奏检查"
    
    def get_penalty(self, layout: LayoutType) -> float:
        """返回布局使用频率的惩罚系数（用太多降低优先级）"""
        count = self.layout_counts.get(layout, 0)
        total = len(self.history) if self.history else 1
        ratio = count / total
        
        # 使用超过 40% 开始惩罚
        if ratio > 0.4:
            return 0.7
        elif ratio > 0.3:
            return 0.85
        elif ratio > 0.2:
            return 0.95
        return 1.0
    
    def check_variety(self) -> Tuple[bool, str]:
        """检查整体多样性是否达标"""
        unique = len(set(self.history))
        if unique < self.MIN_LAYOUT_VARIETY and len(self.history) >= 5:
            return False, f"已生成 {len(self.history)} 页，仅使用 {unique} 种布局，需要增加多样性"
        return True, "多样性达标"


class ConflictResolver:
    """
    冲突解决器：处理多特征同时触发时的优先级仲裁
    
    仲裁优先级（从高到低）：
    1. 用户显式指定（最高优先级）
    2. 图片数量（强信号：有图必须用含图布局）
    3. 对比/时间线关键词（强语义信号）
    4. 关键指标数量（数据展示信号）
    5. 文本长度/结构（弱信号）
    """
    
    PRIORITY_WEIGHTS = {
        "user_override": float('inf'),
        "image_mismatch": 10.0,      # 有图但推荐无图布局 = 严重冲突
        "comparison": 5.0,
        "timeline": 5.0,
        "hero_metrics": 4.0,
        "text_length": 2.0,
    }
    
    def resolve(self, 
                ranked_layouts: List[Tuple[LayoutType, float]],
                features: ContentFeatures,
                rhythm: RhythmController,
                user_preference: Optional[LayoutType] = None
               ) -> LayoutRecommendation:
        """
        综合评分、节奏、冲突解决，输出最终推荐
        """
        # 最高优先级：用户显式指定
        if user_preference:
            allowed, reason = rhythm.is_allowed(user_preference)
            if allowed:
                return LayoutRecommendation(
                    layout=user_preference,
                    confidence=1.0,
                    reasoning=f"用户显式指定: {user_preference.value}"
                )
        
        # 遍历候选布局，综合考虑评分和节奏
        candidates = []
        for layout, base_score in ranked_layouts:
            # 节奏惩罚
            allowed, rhythm_reason = rhythm.is_allowed(layout)
            if not allowed:
                continue
            
            penalty = rhythm.get_penalty(layout)
            final_score = base_score * penalty
            
            # 图片冲突检测
            image_conflict = False
            if features.image_count >= 1 and layout in (
                LayoutType.CONTENT_SINGLE, LayoutType.HERO_PANEL
            ):
                image_conflict = True
                final_score *= 0.3  # 有图却推荐无图布局，大幅降权
            
            candidates.append({
                "layout": layout,
                "score": final_score,
                "base_score": base_score,
                "penalty": penalty,
                "image_conflict": image_conflict,
                "rhythm_reason": rhythm_reason
            })
        
        if not candidates:
            # 所有布局都被节奏禁止，强制选择影响最小的
            fallback = ranked_layouts[0][0]
            return LayoutRecommendation(
                layout=fallback,
                confidence=0.3,
                reasoning="所有候选布局均触发节奏限制，强制选择最高分"
            )
        
        # 按最终分数排序
        candidates.sort(key=lambda x: x["score"], reverse=True)
        best = candidates[0]
        alt = candidates[1] if len(candidates) > 1 else None
        
        reasoning_parts = [
            f"基础匹配度: {best['base_score']:.2f}",
            f"节奏惩罚: {best['penalty']:.2f}",
            f"最终得分: {best['score']:.2f}",
        ]
        if best["image_conflict"]:
            reasoning_parts.append("⚠️ 图片冲突: 有图但推荐无图布局")
        
        return LayoutRecommendation(
            layout=best["layout"],
            confidence=min(best["score"], 1.0),
            reasoning="; ".join(reasoning_parts),
            alternative=alt["layout"] if alt else None,
            alt_confidence=alt["score"] if alt else 0.0
        )


class LayoutManager:
    """
    布局管理器主类
    
    使用示例：
        lm = LayoutManager()
        features = lm.extract_features(title="实验结果", bullets=["..."], images=["fig1.png"])
        rec = lm.recommend(features, user_preference=None)
        print(rec.layout)  # LayoutType.IMAGE_TOP_ANALYSIS
        print(rec.confidence)  # 0.92
        print(rec.reasoning)   # "基础匹配度: 0.95; 节奏惩罚: 1.0; 最终得分: 0.92"
    """
    
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.scorer = LayoutScorer()
        self.rhythm = RhythmController()
        self.resolver = ConflictResolver()
    
    def extract_features(self, title: str, bullets: List[str], images: List[str]) -> ContentFeatures:
        """提取内容特征"""
        return self.extractor.extract(title, bullets, images)
    
    def recommend(self, 
                  features: ContentFeatures,
                  user_preference: Optional[LayoutType] = None
                 ) -> LayoutRecommendation:
        """
        为单页内容推荐最佳布局
        
        Args:
            features: 内容特征向量
            user_preference: 用户/LLM 显式指定的布局偏好（可选）
        
        Returns:
            LayoutRecommendation: 包含推荐布局、置信度、理由、备选
        """
        # 1. 对所有布局评分排序
        ranked = self.scorer.rank(features)
        
        # 2. 冲突解决 + 节奏控制
        recommendation = self.resolver.resolve(
            ranked, features, self.rhythm, user_preference
        )
        
        # 3. 记录使用历史
        self.rhythm.record(recommendation.layout)
        
        return recommendation
    
    def get_rhythm_report(self) -> Dict:
        """获取当前节奏状态报告"""
        variety_ok, variety_msg = self.rhythm.check_variety()
        return {
            "history": [l.value for l in self.rhythm.history],
            "layout_counts": {k.value: v for k, v in self.rhythm.layout_counts.items()},
            "variety_ok": variety_ok,
            "variety_message": variety_msg
        }
    
    def reset(self):
        """重置节奏状态（用于新 deck）"""
        self.rhythm = RhythmController()


# ═══════════════════════════════════════════════════════════════
# 与 SlideDeck 的集成接口
# ═══════════════════════════════════════════════════════════════

def auto_assign_layout(deck, slide_content: dict, user_override: str = None) -> str:
    """
    供 SlideDeck 调用的便捷函数
    
    Args:
        deck: SlideDeck 实例（用于读取设计契约中的节奏状态）
        slide_content: {"title": str, "bullets": List[str], "images": List[str]}
        user_override: 用户显式指定的布局名称（可选）
    
    Returns:
        str: 布局类型名称
    """
    lm = LayoutManager()
    
    # 恢复 deck 的节奏状态（如果有）
    if hasattr(deck, '_layout_history'):
        lm.rhythm.history = deck._layout_history
        lm.rhythm.layout_counts = deck._layout_counts
    
    features = lm.extract_features(
        title=slide_content.get("title", ""),
        bullets=slide_content.get("bullets", []),
        images=slide_content.get("images", [])
    )
    
    override_enum = LayoutType(user_override) if user_override else None
    rec = lm.recommend(features, user_override=override_enum)
    
    # 保存状态回 deck
    deck._layout_history = lm.rhythm.history
    deck._layout_counts = lm.rhythm.layout_counts
    
    return rec.layout.value
