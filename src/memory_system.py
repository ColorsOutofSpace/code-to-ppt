"""
Memory System: 三层记忆结构

核心设计：
1. User Profile（用户画像）：跨项目、跨会话的稳定偏好
2. Error Registry（错误登记册）：执行中发现的问题及根因
3. Insight Cache（洞察缓存）：后期发现的有价值洞察

持久化：~/.config/code-to-ppt/memory/{user_id}.json
自动提取：从对话和执行日志中自动提取，无需用户手动记录
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path


# ═══════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════

@dataclass
class UserIdentity:
    """用户身份信息"""
    institution: str = ""
    department: str = ""
    role: str = ""  # 本科生/硕士生/博士生/产品经理/...


@dataclass
class DesignDNA:
    """设计 DNA：稳定的设计偏好"""
    preferred_themes: List[str] = field(default_factory=list)
    color_temperature: str = "neutral"  # cool/warm/neutral
    density_preference: str = "medium"  # high/medium/low
    layout_biases: List[str] = field(default_factory=list)
    font_preferences: Dict[str, str] = field(default_factory=lambda: {
        "chinese": "Microsoft YaHei",
        "english": "Arial"
    })


@dataclass
class ContentPatterns:
    """内容模式：用户常见的内容结构"""
    common_sections: List[str] = field(default_factory=list)
    typical_metrics: List[str] = field(default_factory=list)
    frequent_comparisons: List[str] = field(default_factory=list)
    preferred_languages: List[str] = field(default_factory=lambda: ["zh"])


@dataclass
class CommunicationStyle:
    """沟通风格"""
    response_speed: str = "medium"  # fast/medium/thorough
    detail_level: str = "medium"    # high/medium/low
    correction_tolerance: str = "medium"  # high/medium/low


@dataclass
class UserProfile:
    """用户画像：第一层记忆"""
    identity: UserIdentity = field(default_factory=UserIdentity)
    design_dna: DesignDNA = field(default_factory=DesignDNA)
    content_patterns: ContentPatterns = field(default_factory=ContentPatterns)
    communication_style: CommunicationStyle = field(default_factory=CommunicationStyle)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        return cls(
            identity=UserIdentity(**data.get("identity", {})),
            design_dna=DesignDNA(**data.get("design_dna", {})),
            content_patterns=ContentPatterns(**data.get("content_patterns", {})),
            communication_style=CommunicationStyle(**data.get("communication_style", {}))
        )


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    timestamp: str
    session_id: str
    error_type: str
    severity: str  # high/medium/low
    description: str
    root_cause: str
    prevention: str
    affected_slides: List[int] = field(default_factory=list)
    fix_applied: str = ""
    status: str = "open"  # open/resolved/verified
    lessons_learned: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InsightRecord:
    """洞察记录"""
    insight_id: str
    timestamp: str
    session_id: str
    insight: str
    trigger: str  # 什么触发了这个洞察
    confidence: float = 0.5  # 0.0-1.0
    application_scope: str = ""  # 适用范围
    prerequisites: List[str] = field(default_factory=list)
    usage_count: int = 0  # 被应用次数
    last_used: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SessionRecord:
    """会话记录"""
    session_id: str
    timestamp: str
    topic: str
    deck_type: str  # thesis/pitch/report/...
    slide_count: int = 0
    key_decisions: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    insights_generated: List[str] = field(default_factory=list)
    outcome: str = ""  # success/partial/failure
    user_feedback: str = ""


@dataclass
class MemoryBundle:
    """完整记忆包"""
    user_id: str
    created_at: str
    updated_at: str
    user_profile: UserProfile = field(default_factory=UserProfile)
    error_registry: List[ErrorRecord] = field(default_factory=list)
    insight_cache: List[InsightRecord] = field(default_factory=list)
    session_history: List[SessionRecord] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_profile": self.user_profile.to_dict(),
            "error_registry": [e.to_dict() for e in self.error_registry],
            "insight_cache": [i.to_dict() for i in self.insight_cache],
            "session_history": [asdict(s) for s in self.session_history]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryBundle":
        return cls(
            user_id=data.get("user_id", "anonymous"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            user_profile=UserProfile.from_dict(data.get("user_profile", {})),
            error_registry=[ErrorRecord(**e) for e in data.get("error_registry", [])],
            insight_cache=[InsightRecord(**i) for i in data.get("insight_cache", [])],
            session_history=[SessionRecord(**s) for s in data.get("session_history", [])]
        )


# ═══════════════════════════════════════════
# 记忆管理器
# ═══════════════════════════════════════════

class MemoryManager:
    """
    记忆管理器
    
    职责：
    1. 加载/保存记忆
    2. 自动提取偏好和洞察
    3. 生成上下文注入 prompt
    4. 记忆清理和归档
    """
    
    DEFAULT_MEMORY_DIR = Path.home() / ".config" / "code-to-ppt" / "memory"
    
    def __init__(self, user_id: str = "anonymous"):
        self.user_id = user_id
        self.memory_dir = self.DEFAULT_MEMORY_DIR
        self.memory_file = self.memory_dir / f"{user_id}.json"
        self.bundle: Optional[MemoryBundle] = None
        
        self._ensure_dir()
        self._load()
    
    def _ensure_dir(self):
        """确保记忆目录存在"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def _load(self):
        """加载记忆文件"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.bundle = MemoryBundle.from_dict(data)
                print(f"[记忆加载] 已加载用户 {self.user_id} 的记忆，"
                      f"共 {len(self.bundle.error_registry)} 条错误，"
                      f"{len(self.bundle.insight_cache)} 条洞察")
            except Exception as e:
                print(f"[记忆加载] 加载失败: {e}，创建新记忆")
                self.bundle = self._create_new_bundle()
        else:
            self.bundle = self._create_new_bundle()
    
    def _create_new_bundle(self) -> MemoryBundle:
        """创建新记忆包"""
        now = datetime.now().isoformat()
        return MemoryBundle(
            user_id=self.user_id,
            created_at=now,
            updated_at=now
        )
    
    def save(self):
        """保存记忆到文件"""
        if not self.bundle:
            return
        
        self.bundle.updated_at = datetime.now().isoformat()
        
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.bundle.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"[记忆保存] 已保存到 {self.memory_file}")
        except Exception as e:
            print(f"[记忆保存] 保存失败: {e}")
    
    # ═══ User Profile 管理 ═══
    
    def update_profile(self, **kwargs):
        """更新用户画像"""
        if not self.bundle:
            return
        
        profile = self.bundle.user_profile
        
        # 更新身份
        if "institution" in kwargs:
            profile.identity.institution = kwargs["institution"]
        if "department" in kwargs:
            profile.identity.department = kwargs["department"]
        if "role" in kwargs:
            profile.identity.role = kwargs["role"]
        
        # 更新设计 DNA
        if "preferred_themes" in kwargs:
            profile.design_dna.preferred_themes = kwargs["preferred_themes"]
        if "color_temperature" in kwargs:
            profile.design_dna.color_temperature = kwargs["color_temperature"]
        if "density_preference" in kwargs:
            profile.design_dna.density_preference = kwargs["density_preference"]
        if "layout_biases" in kwargs:
            profile.design_dna.layout_biases = kwargs["layout_biases"]
        
        # 更新内容模式
        if "common_sections" in kwargs:
            profile.content_patterns.common_sections = kwargs["common_sections"]
        if "typical_metrics" in kwargs:
            profile.content_patterns.typical_metrics = kwargs["typical_metrics"]
        
        self.save()
    
    def infer_preference_from_choice(self, choice: str, category: str):
        """
        从用户选择中推断偏好
        
        示例：
            infer_preference_from_choice("academic", "theme")
            → 更新 preferred_themes += ["academic"]
        """
        if not self.bundle:
            return
        
        profile = self.bundle.user_profile
        
        if category == "theme":
            if choice not in profile.design_dna.preferred_themes:
                profile.design_dna.preferred_themes.append(choice)
        
        elif category == "layout":
            if choice not in profile.design_dna.layout_biases:
                profile.design_dna.layout_biases.append(choice)
        
        elif category == "color_temperature":
            profile.design_dna.color_temperature = choice
        
        elif category == "density":
            profile.design_dna.density_preference = choice
        
        self.save()
    
    # ═══ Error Registry 管理 ═══
    
    def record_error(self, error_type: str, description: str, root_cause: str,
                    prevention: str, affected_slides: List[int] = None,
                    severity: str = "medium", session_id: str = "") -> str:
        """记录错误"""
        if not self.bundle:
            return ""
        
        error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        error = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            error_type=error_type,
            severity=severity,
            description=description,
            root_cause=root_cause,
            prevention=prevention,
            affected_slides=affected_slides or [],
            status="open"
        )
        
        self.bundle.error_registry.append(error)
        self.save()
        
        return error_id
    
    def resolve_error(self, error_id: str, fix_applied: str, 
                     lessons_learned: str = ""):
        """标记错误为已解决"""
        if not self.bundle:
            return
        
        for error in self.bundle.error_registry:
            if error.error_id == error_id:
                error.status = "resolved"
                error.fix_applied = fix_applied
                error.lessons_learned = lessons_learned
                self.save()
                return
    
    def get_relevant_errors(self, context: str = "", limit: int = 5) -> List[ErrorRecord]:
        """获取与当前场景相关的错误"""
        if not self.bundle:
            return []
        
        # 简单的关键词匹配（实际可用 embedding）
        relevant = []
        for error in self.bundle.error_registry:
            if context.lower() in error.description.lower() or \
               context.lower() in error.error_type.lower():
                relevant.append(error)
        
        # 按严重性和时间排序
        severity_order = {"high": 0, "medium": 1, "low": 2}
        relevant.sort(key=lambda e: (severity_order.get(e.severity, 1), e.timestamp), 
                     reverse=True)
        
        return relevant[:limit]
    
    # ═══ Insight Cache 管理 ═══
    
    def record_insight(self, insight: str, trigger: str, 
                      application_scope: str = "", 
                      prerequisites: List[str] = None,
                      session_id: str = "") -> str:
        """记录洞察"""
        if not self.bundle:
            return ""
        
        insight_id = f"ins_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        record = InsightRecord(
            insight_id=insight_id,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            insight=insight,
            trigger=trigger,
            application_scope=application_scope,
            prerequisites=prerequisites or []
        )
        
        self.bundle.insight_cache.append(record)
        self.save()
        
        return insight_id
    
    def use_insight(self, insight_id: str):
        """标记洞察被使用"""
        if not self.bundle:
            return
        
        for insight in self.bundle.insight_cache:
            if insight.insight_id == insight_id:
                insight.usage_count += 1
                insight.last_used = datetime.now().isoformat()
                # 增加置信度
                insight.confidence = min(insight.confidence + 0.1, 1.0)
                self.save()
                return
    
    def get_relevant_insights(self, context: str = "", deck_type: str = "",
                             limit: int = 5) -> List[InsightRecord]:
        """获取与当前场景相关的洞察"""
        if not self.bundle:
            return []
        
        relevant = []
        for insight in self.bundle.insight_cache:
            # 匹配应用场景
            if deck_type and deck_type in insight.application_scope:
                relevant.append(insight)
            # 匹配关键词
            elif context.lower() in insight.insight.lower():
                relevant.append(insight)
        
        # 按置信度和使用次数排序
        relevant.sort(key=lambda i: (i.confidence, i.usage_count), reverse=True)
        
        return relevant[:limit]
    
    # ═══ Session History 管理 ═══
    
    def start_session(self, session_id: str, topic: str, deck_type: str):
        """开始新会话记录"""
        if not self.bundle:
            return
        
        session = SessionRecord(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            topic=topic,
            deck_type=deck_type
        )
        
        self.bundle.session_history.append(session)
        self.save()
    
    def end_session(self, session_id: str, outcome: str, 
                   user_feedback: str = ""):
        """结束会话记录"""
        if not self.bundle:
            return
        
        for session in self.bundle.session_history:
            if session.session_id == session_id:
                session.outcome = outcome
                session.user_feedback = user_feedback
                self.save()
                return
    
    # ═══ 上下文生成 ═══
    
    def generate_context_injection(self, deck_type: str = "", 
                                  current_phase: str = "") -> str:
        """
        生成供 LLM 注入的上下文摘要
        
        这个摘要将在每个 prompt 中注入，确保 LLM 不遗忘用户偏好和过往教训
        """
        if not self.bundle:
            return ""
        
        lines = ["═══ 用户记忆上下文 ═══"]
        
        # User Profile
        profile = self.bundle.user_profile
        lines.extend([
            f"用户: {profile.identity.institution} {profile.identity.department} {profile.identity.role}",
            f"设计偏好: 主题={profile.design_dna.preferred_themes}, "
            f"色温={profile.design_dna.color_temperature}, "
            f"密度={profile.design_dna.density_preference}",
            f"常用布局: {', '.join(profile.design_dna.layout_biases)}",
        ])
        
        # 相关错误（提醒不要重复犯错）
        relevant_errors = self.get_relevant_errors(context=current_phase)
        if relevant_errors:
            lines.append("\n═══ 过往错误（避免重复）═══")
            for error in relevant_errors[:3]:
                lines.append(f"⚠️ [{error.error_type}] {error.description}")
                lines.append(f"   根因: {error.root_cause}")
                lines.append(f"   预防: {error.prevention}")
        
        # 相关洞察（应用过往经验）
        relevant_insights = self.get_relevant_insights(
            context=current_phase, deck_type=deck_type
        )
        if relevant_insights:
            lines.append("\n═══ 过往洞察（建议应用）═══")
            for insight in relevant_insights[:3]:
                lines.append(f"💡 {insight.insight}")
                lines.append(f"   触发: {insight.trigger}")
        
        return "\n".join(lines)
    
    def generate_user_summary(self) -> str:
        """生成用户画像摘要（供用户查看）"""
        if not self.bundle:
            return "暂无记忆"
        
        profile = self.bundle.user_profile
        
        lines = [
            f"# 用户画像: {self.user_id}",
            f"",
            f"**身份**: {profile.identity.institution} {profile.identity.department} {profile.identity.role}",
            f"",
            f"**设计偏好**:",
            f"- 常用主题: {', '.join(profile.design_dna.preferred_themes)}",
            f"- 色温: {profile.design_dna.color_temperature}",
            f"- 密度: {profile.design_dna.density_preference}",
            f"- 偏好布局: {', '.join(profile.design_dna.layout_biases)}",
            f"",
            f"**历史统计**:",
            f"- 总会话: {len(self.bundle.session_history)}",
            f"- 已知错误: {len(self.bundle.error_registry)} ({sum(1 for e in self.bundle.error_registry if e.status=='open')} 未解决)",
            f"- 积累洞察: {len(self.bundle.insight_cache)}",
        ]
        
        return "\n".join(lines)
    
    # ═══ 记忆清理 ═══
    
    def clean_old_memories(self, days: int = 90):
        """清理过旧的记忆"""
        if not self.bundle:
            return
        
        cutoff = datetime.now().timestamp() - days * 24 * 3600
        
        # 清理已解决的旧错误
        self.bundle.error_registry = [
            e for e in self.bundle.error_registry
            if e.status != "resolved" or 
            datetime.fromisoformat(e.timestamp).timestamp() > cutoff
        ]
        
        # 清理低置信度的旧洞察
        self.bundle.insight_cache = [
            i for i in self.bundle.insight_cache
            if i.confidence > 0.3 or
            datetime.fromisoformat(i.timestamp).timestamp() > cutoff
        ]
        
        self.save()


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def get_memory_manager(user_id: str = "anonymous") -> MemoryManager:
    """获取记忆管理器实例"""
    return MemoryManager(user_id)


def extract_from_conversation(conversation: List[Dict], 
                              manager: MemoryManager) -> Dict:
    """
    从对话历史中自动提取偏好和洞察
    
    示例输入：
        [
            {"role": "user", "content": "我喜欢冷色调"},
            {"role": "assistant", "content": "已记录"},
            {"role": "user", "content": "上次那个布局不错"},
        ]
    
    提取结果：
        {"color_temperature": "cool", "layout_biases": ["two_column_compare"]}
    """
    extracted = {}
    
    preference_patterns = {
        "color_temperature": {
            "cool": ["冷色", "蓝色", "清爽", "cool"],
            "warm": ["暖色", "红色", "橙色", "warm"],
        },
        "density": {
            "high": ["密集", "详细", "多内容", "high density"],
            "low": ["简洁", "留白", "少内容", "minimal"],
        }
    }
    
    for msg in conversation:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            
            # 提取色温偏好
            for temp, keywords in preference_patterns["color_temperature"].items():
                if any(kw in content for kw in keywords):
                    extracted["color_temperature"] = temp
                    manager.infer_preference_from_choice(temp, "color_temperature")
            
            # 提取密度偏好
            for density, keywords in preference_patterns["density"].items():
                if any(kw in content for kw in keywords):
                    extracted["density_preference"] = density
                    manager.infer_preference_from_choice(density, "density")
    
    return extracted
