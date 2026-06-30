"""
DesignContract: 长程一致性保证系统

核心设计：
1. 状态机管理：记录全局设计决策（色板、字体、布局节奏）
2. 验证钩子：每页生成前/后自动检查一致性
3. 自修复机制：发现漂移时自动纠正或告警
4. 上下文压缩：将设计契约压缩为 LLM 可快速引用的形式

使用场景：
- SlideDeck 在生成每一页前，查询 DesignContract 获取当前约束
- 生成后，更新 DesignContract 记录新状态
- 全部生成后，运行全局一致性检查
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import json


class ThemeType(Enum):
    ACADEMIC = "academic"
    BUSINESS = "business"
    MEDICAL = "medical"
    TECH = "tech"
    CREATIVE = "creative"


class LayoutType(Enum):
    COVER = "cover"
    OUTLINE = "outline"
    SECTION_DIVIDER = "section_divider"
    TWO_COLUMN_COMPARE = "two_column_compare"
    IMAGE_TOP_ANALYSIS = "image_top_analysis"
    IMAGE_LEFT_TEXT_RIGHT = "image_left_text_right"
    THREE_IMAGES = "three_images"
    TIMELINE = "timeline"
    HERO_PANEL = "hero_panel"
    CONTENT_SINGLE = "content_single"
    CONTENT_DUAL = "content_dual"
    SUMMARY = "summary"
    THANKYOU = "thankyou"


@dataclass
class ColorPalette:
    """四层色板"""
    primary: List[str] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)
    neutral: List[str] = field(default_factory=list)
    semantic: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_theme(cls, theme: ThemeType) -> "ColorPalette":
        """根据主题类型生成默认色板"""
        palettes = {
            ThemeType.ACADEMIC: cls(
                primary=["#2C3E50", "#34495E"],
                secondary=["#3498DB", "#F39C12"],
                neutral=["#1A1A1A", "#6B7B8D", "#EDF2F8", "#FFFFFF"],
                semantic={"positive": "#27AE60", "warning": "#C0392B", "contrast": "#D4A84B"}
            ),
            ThemeType.BUSINESS: cls(
                primary=["#1B2A4A", "#2C3E50"],
                secondary=["#D4A84B", "#C0392B"],
                neutral=["#1A1A1A", "#6B7B8D", "#EDF2F8", "#FFFFFF"],
                semantic={"positive": "#27AE60", "warning": "#C0392B", "contrast": "#D4A84B"}
            ),
            ThemeType.MEDICAL: cls(
                primary=["#1A3C4A", "#2C5F6E"],
                secondary=["#2EA6D3", "#27AE60"],
                neutral=["#1A1A1A", "#6B7B8D", "#EDF2F8", "#FFFFFF"],
                semantic={"positive": "#27AE60", "warning": "#C0392B", "contrast": "#D4A84B"}
            ),
            ThemeType.TECH: cls(
                primary=["#1A1A2E", "#2D2D44"],
                secondary=["#4A90D9", "#E67E22"],
                neutral=["#1A1A1A", "#6B7B8D", "#EDF2F8", "#FFFFFF"],
                semantic={"positive": "#27AE60", "warning": "#C0392B", "contrast": "#D4A84B"}
            ),
            ThemeType.CREATIVE: cls(
                primary=["#2D1B69", "#4A2C8A"],
                secondary=["#E74C3C", "#F1C40F"],
                neutral=["#1A1A1A", "#6B7B8D", "#EDF2F8", "#FFFFFF"],
                semantic={"positive": "#2EA6D3", "warning": "#C0392B", "contrast": "#D4A84B"}
            ),
        }
        return palettes.get(theme, palettes[ThemeType.ACADEMIC])


@dataclass
class Typography:
    """字体约定"""
    chinese: str = "Microsoft YaHei"
    english: str = "Arial"
    title_size: int = 27
    subtitle_size: int = 11
    body_size: int = 9.5
    hero_size: int = 42
    footer_size: int = 7
    line_spacing: float = 1.45
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SlideState:
    """单页状态记录"""
    slide_number: int
    layout: LayoutType
    title: str
    accent_color_used: str = ""           # 这页使用的强调线颜色
    layout_pattern: str = ""              # 布局模式（用于多样性检查）
    key_metrics: List[str] = field(default_factory=list)
    images_used: List[str] = field(default_factory=list)


class DesignContract:
    """
    设计契约：全局一致性状态机
    
    核心职责：
    1. 锁定设计决策（色板、字体、间距）
    2. 记录生成历史（每页的布局、颜色、节奏）
    3. 提供验证钩子（生成前检查、生成后校验）
    4. 生成上下文摘要（供 LLM 快速引用）
    """
    
    # 反 AI 味规则（必须全局一致执行）
    ANTI_AI_RULES = {
        "no_left_vertical_bar": True,      # 无左侧竖线装饰
        "no_box_shadow": True,             # 无投影效果
        "min_layout_variety": 3,           # 至少3种不同布局
        "footer_short_line": True,         # 页脚是短线
        "semantic_accent_colors": True,    # 颜色语义化
        "concrete_data": True,             # 数据具体
        "no_clipart": True,                # 无花哨图标
        "max_bullets_per_slide": 8,        # 每页最多8行
        "min_body_font_size": 9.5,         # 正文字号最小9.5pt
    }
    
    # 布局节奏规则
    RHYTHM_RULES = {
        "max_consecutive_same_layout": 2,
        "hero_spacing_min": 2,             # hero 面板之间至少间隔2页
        "section_divider_spacing": 1,      # 章节过渡页后至少1页内容页
        "band_separator_interval": 3,      # 每3页内容页建议插入色带
    }
    
    def __init__(self, theme: ThemeType = ThemeType.ACADEMIC):
        # ═══ 锁定设计决策（一旦设定，全程不变）═══
        self.theme = theme
        self.color_palette = ColorPalette.from_theme(theme)
        self.typography = Typography()
        
        # 用户自定义覆盖（可选）
        self.custom_colors: Dict[str, str] = {}
        self.custom_fonts: Dict[str, str] = {}
        
        # ═══ 生成状态（随页面生成逐步更新）═══
        self.slide_history: List[SlideState] = []
        self.layout_counts: Dict[LayoutType, int] = {}
        self.accent_color_counts: Dict[str, int] = {}
        self.total_slides: int = 0
        
        # ═══ 一致性检查结果 ═══
        self.violations: List[Dict] = []
        self.warnings: List[Dict] = []
    
    # ═══════════════════════════════════════════
    # 公开 API：供 SlideDeck 调用
    # ═══════════════════════════════════════════
    
    def get_color(self, role: str) -> str:
        """
        获取颜色（带自定义覆盖检查）
        
        Args:
            role: "primary", "secondary", "neutral", "positive", "warning", "contrast"
        
        Returns:
            hex 颜色值
        """
        if role in self.custom_colors:
            return self.custom_colors[role]
        
        if role in self.color_palette.semantic:
            return self.color_palette.semantic[role]
        elif role == "primary":
            return self.color_palette.primary[0]
        elif role == "secondary":
            return self.color_palette.secondary[0]
        elif role == "neutral":
            return self.color_palette.neutral[1]  # 默认灰色
        elif role == "background":
            return self.color_palette.neutral[2]   # 浅底
        elif role == "white":
            return "#FFFFFF"
        
        return "#000000"  # fallback
    
    def get_font(self, script: str = "chinese") -> str:
        """获取字体"""
        if script in self.custom_fonts:
            return self.custom_fonts[script]
        return getattr(self.typography, script, "Microsoft YaHei")
    
    def validate_before_build(self, slide_config: Dict) -> Tuple[bool, List[str]]:
        """
        生成单页前的验证钩子
        
        Args:
            slide_config: {"layout": str, "title": str, "bullets": List[str], ...}
        
        Returns:
            (是否通过, [错误信息列表])
        """
        errors = []
        layout_name = slide_config.get("layout", "")
        bullets = slide_config.get("bullets", [])
        
        # 规则 1：bullet 数量检查
        if len(bullets) > self.ANTI_AI_RULES["max_bullets_per_slide"]:
            errors.append(
                f"❌ 规则违反：bullet 数量 {len(bullets)} 超过上限 "
                f"({self.ANTI_AI_RULES['max_bullets_per_slide']})"
            )
        
        # 规则 2：布局多样性检查（连续同布局）
        layout_type = LayoutType(layout_name) if layout_name else LayoutType.CONTENT_SINGLE
        consecutive = self._count_consecutive_layout(layout_type)
        if consecutive >= self.RHYTHM_RULES["max_consecutive_same_layout"]:
            errors.append(
                f"⚠️ 节奏警告：连续 {consecutive} 页使用 {layout_name}，"
                f"建议更换布局打破单调"
            )
        
        # 规则 3：hero 面板间距检查
        if layout_type == LayoutType.HERO_PANEL:
            last_hero = self._find_last_layout(LayoutType.HERO_PANEL)
            if last_hero and (self.total_slides - last_hero) < self.RHYTHM_RULES["hero_spacing_min"]:
                errors.append(
                    f"⚠️ 节奏警告：距上次 hero 面板仅 {self.total_slides - last_hero} 页，"
                    f"建议间隔 ≥{self.RHYTHM_RULES['hero_spacing_min']} 页"
                )
        
        # 规则 4：语义颜色一致性检查
        accent = slide_config.get("accent_color_semantic", "")
        if accent and accent not in self.color_palette.semantic:
            errors.append(
                f"⚠️ 颜色警告：'{accent}' 不在预定义语义色中 "
                f"({list(self.color_palette.semantic.keys())})"
            )
        
        is_pass = not any(e.startswith("❌") for e in errors)
        return is_pass, errors
    
    def record_after_build(self, slide_state: SlideState):
        """
        生成单页后的状态更新
        
        Args:
            slide_state: 这页的实际状态
        """
        self.slide_history.append(slide_state)
        self.total_slides += 1
        
        # 更新布局计数
        self.layout_counts[slide_state.layout] = \
            self.layout_counts.get(slide_state.layout, 0) + 1
        
        # 更新颜色计数
        if slide_state.accent_color_used:
            self.accent_color_counts[slide_state.accent_color_used] = \
                self.accent_color_counts.get(slide_state.accent_color_used, 0) + 1
    
    def validate_global(self) -> Tuple[bool, List[Dict]]:
        """
        全部生成后的全局一致性检查
        
        Returns:
            (是否通过, [违规详情列表])
        """
        violations = []
        
        # 检查 1：布局多样性
        unique_layouts = len(self.layout_counts)
        if unique_layouts < self.ANTI_AI_RULES["min_layout_variety"]:
            violations.append({
                "severity": "error",
                "rule": "min_layout_variety",
                "message": f"仅使用 {unique_layouts} 种布局，"
                          f"要求 ≥{self.ANTI_AI_RULES['min_layout_variety']} 种",
                "suggestion": f"建议增加: {self._suggest_missing_layouts()}"
            })
        
        # 检查 2：无左侧竖线装饰（反 AI 味）
        # 注：这个需要在视觉审查阶段检查，此处记录规则
        violations.append({
            "severity": "info",
            "rule": "no_left_vertical_bar",
            "message": "请在视觉审查阶段确认无左侧竖线装饰",
            "suggestion": "使用卡片顶部横线（0.03\"）替代"
        })
        
        # 检查 3：页脚一致性
        # 注：这个由代码生成保证，但记录检查点
        violations.append({
            "severity": "info", 
            "rule": "footer_short_line",
            "message": "请在视觉审查阶段确认页脚为短线（~1.8\"）",
            "suggestion": "检查 ft() 中的线长度参数"
        })
        
        # 检查 4：配色一致性
        if len(self.accent_color_counts) > len(self.color_palette.semantic) + 2:
            violations.append({
                "severity": "warning",
                "rule": "color_consistency",
                "message": f"使用了 {len(self.accent_color_counts)} 种不同强调色，"
                          f"超过预定义语义色数量 ({len(self.color_palette.semantic)})",
                "suggestion": "合并相似颜色，严格按语义色板使用"
            })
        
        # 检查 5：章节过渡页检查
        section_dividers = self.layout_counts.get(LayoutType.SECTION_DIVIDER, 0)
        content_slides = sum(1 for s in self.slide_history 
                           if s.layout not in (LayoutType.COVER, LayoutType.OUTLINE, 
                                              LayoutType.SECTION_DIVIDER, LayoutType.THANKYOU))
        if content_slides > 8 and section_dividers == 0:
            violations.append({
                "severity": "warning",
                "rule": "section_structure",
                "message": f"{content_slides} 页内容无章节过渡页，结构可能不清晰",
                "suggestion": "在主要章节切换处插入 section_divider"
            })
        
        is_pass = not any(v["severity"] == "error" for v in violations)
        self.violations = violations
        return is_pass, violations
    
    def get_context_summary(self, max_length: int = 800) -> str:
        """
        生成供 LLM 快速引用的上下文摘要
        
        这个摘要将作为 system prompt 的一部分注入到每页生成中，
        确保 LLM 在长程任务中不遗忘全局约定。
        
        Returns:
            压缩后的设计契约文本
        """
        lines = [
            "═══ 设计契约（Design Contract）═══",
            f"主题: {self.theme.value}",
            f"色板:",
            f"  主色: {self.color_palette.primary[0]}",
            f"  辅色: {', '.join(self.color_palette.secondary[:2])}",
            f"  语义: 正面={self.get_color('positive')}, "
            f"警告={self.get_color('warning')}, 对比={self.get_color('contrast')}",
            f"字体: 中文={self.get_font('chinese')}, 英文={self.get_font('english')}",
            f"已生成: {self.total_slides} 页",
            f"布局分布: {', '.join(f'{k.value}({v})' for k, v in self.layout_counts.items())}",
            f"",
            "═══ 反 AI 味规则（必须遵守）═══",
            f"✗ 无左侧竖线装饰（用顶部横线 0.03\"）",
            f"✗ 无 box shadow/投影",
            f"✓ 至少 {self.ANTI_AI_RULES['min_layout_variety']} 种布局（已用 {len(self.layout_counts)} 种）",
            f"✓ 页脚短线 (~1.8\")",
            f"✓ 颜色语义化（通用=辅色，创新=绿色，问题=红色）",
            f"✓ 每页 ≤{self.ANTI_AI_RULES['max_bullets_per_slide']} 行 bullet",
            f"",
            "═══ 节奏状态 ═══",
        ]
        
        # 添加最近3页的布局历史（防止连续同布局）
        recent = self.slide_history[-3:]
        for s in recent:
            lines.append(f"  P{s.slide_number}: {s.layout.value}")
        
        # 添加当前约束
        lines.extend([
            f"",
            f"═══ 当前约束 ═══",
            f"下一页应避免: {self._get_forbidden_next_layouts()}",
        ])
        
        summary = "\n".join(lines)
        if len(summary) > max_length:
            # 压缩：只保留核心色板和最近2页
            summary = self._compress_summary()
        
        return summary
    
    def export_to_json(self) -> str:
        """导出完整状态为 JSON（用于持久化/调试）"""
        state = {
            "theme": self.theme.value,
            "color_palette": self.color_palette.to_dict(),
            "typography": self.typography.to_dict(),
            "custom_colors": self.custom_colors,
            "slide_history": [
                {
                    "slide_number": s.slide_number,
                    "layout": s.layout.value,
                    "title": s.title,
                    "accent_color": s.accent_color_used,
                }
                for s in self.slide_history
            ],
            "layout_counts": {k.value: v for k, v in self.layout_counts.items()},
            "total_slides": self.total_slides,
            "violations": self.violations,
        }
        return json.dumps(state, indent=2, ensure_ascii=False)
    
    # ═══════════════════════════════════════════
    # 内部辅助方法
    # ═══════════════════════════════════════════
    
    def _count_consecutive_layout(self, layout: LayoutType) -> int:
        """统计目标布局的连续出现次数"""
        count = 0
        for state in reversed(self.slide_history):
            if state.layout == layout:
                count += 1
            else:
                break
        return count
    
    def _find_last_layout(self, layout: LayoutType) -> Optional[int]:
        """查找某布局最后一次出现的页号"""
        for state in reversed(self.slide_history):
            if state.layout == layout:
                return state.slide_number
        return None
    
    def _suggest_missing_layouts(self) -> str:
        """建议尚未使用的布局"""
        all_layouts = set(LayoutType) - {LayoutType.COVER, LayoutType.THANKYOU}
        used = set(self.layout_counts.keys())
        missing = all_layouts - used
        return ", ".join(l.value for l in missing) if missing else "无"
    
    def _get_forbidden_next_layouts(self) -> str:
        """获取下一页应避免使用的布局"""
        forbidden = []
        
        # 如果连续2页同布局，禁止再用
        if self.slide_history:
            last_layout = self.slide_history[-1].layout
            consecutive = self._count_consecutive_layout(last_layout)
            if consecutive >= self.RHYTHM_RULES["max_consecutive_same_layout"]:
                forbidden.append(f"{last_layout.value}（已连续{consecutive}页）")
        
        # 如果上次是 hero，本次避免 hero
        if self.slide_history and self.slide_history[-1].layout == LayoutType.HERO_PANEL:
            forbidden.append("hero_panel（距上次太近）")
        
        return ", ".join(forbidden) if forbidden else "无"
    
    def _compress_summary(self) -> str:
        """生成压缩版摘要（更短）"""
        lines = [
            f"设计契约: {self.theme.value} | "
            f"主色={self.color_palette.primary[0]} | "
            f"正面={self.get_color('positive')} 警告={self.get_color('warning')}",
            f"已生成 {self.total_slides} 页 | "
            f"布局: {', '.join(f'{k.value}:{v}' for k, v in list(self.layout_counts.items())[-3:])}",
            f"约束: 无竖线装饰, 无投影, ≤{self.ANTI_AI_RULES['max_bullets_per_slide']}行, "
            f"页脚短线, 语义配色",
        ]
        if self.slide_history:
            last = self.slide_history[-1]
            lines.append(f"上一页: P{last.slide_number} {last.layout.value}")
        return "\n".join(lines)


# ═══════════════════════════════════════════
# 与 SlideDeck 的集成示例
# ═══════════════════════════════════════════

class SlideDeckWithContract:
    """
    集成 DesignContract 的 SlideDeck 示例
    
    展示了如何在长程生成中使用 DesignContract 保证一致性
    """
    
    def __init__(self, theme: ThemeType = ThemeType.ACADEMIC):
        self.contract = DesignContract(theme)
        self.slides: List[Dict] = []
    
    def add_slide(self, layout: str, title: str, bullets: List[str], **kwargs):
        """
        添加单页，自动经过 DesignContract 验证
        """
        slide_config = {
            "layout": layout,
            "title": title,
            "bullets": bullets,
            **kwargs
        }
        
        # 1. 生成前验证
        is_pass, errors = self.contract.validate_before_build(slide_config)
        if not is_pass:
            raise ValueError(f"设计契约验证失败: {'; '.join(errors)}")
        
        # 2. 将设计契约摘要注入 prompt（供 LLM 参考）
        context = self.contract.get_context_summary()
        # ... 这里将 context 和 slide_config 一起传给 LLM ...
        
        # 3. 模拟生成（实际由 LLM 执行）
        slide_data = self._generate_slide(layout, title, bullets, **kwargs)
        
        # 4. 记录状态
        slide_state = SlideState(
            slide_number=self.contract.total_slides + 1,
            layout=LayoutType(layout),
            title=title,
            accent_color_used=kwargs.get("accent_color_semantic", ""),
        )
        self.contract.record_after_build(slide_state)
        
        self.slides.append(slide_data)
        return slide_data
    
    def _generate_slide(self, layout, title, bullets, **kwargs):
        """模拟生成（实际由 LLM + 声明式引擎执行）"""
        return {"layout": layout, "title": title, "bullets": bullets}
    
    def finalize(self) -> Tuple[bool, List[Dict]]:
        """
        全部生成后的全局检查
        """
        is_pass, violations = self.contract.validate_global()
        return is_pass, violations
    
    def get_contract_report(self) -> str:
        """获取完整的设计契约报告"""
        return self.contract.export_to_json()

