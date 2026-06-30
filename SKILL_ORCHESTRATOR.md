---
name: code-to-ppt-orchestrator
description: |
  认知增强型 PPT 制作 orchestrator。通过结构化拷打挖掘真实需求，
  生成可交互的进化计划，跨会话记忆用户偏好与错误，
  全链路多 Agent 对抗审查。前置增强层，驱动 code-to-ppt 执行。
---

# code-to-ppt：认知增强型 PPT 制作系统

## 1. Overview

本 skill 是 `code-to-ppt` 的**前置增强层**，不是替代它，而是让它的产出**更懂你、更少错、更有说服力**。

核心创新：**从"你告诉我做什么"转变为"我帮你发现该做什么"**。

传统流程：
```
用户说需求 → AI 直接做 → 用户发现不对 → 反复修改
```

本 skill 流程：
```
用户说需求 → [拷打引擎] 挖掘真实意图 → [计划管理器] 生成可修改计划
    → [记忆系统] 注入偏好和教训 → [执行层] 执行生成
    → [反思引擎] 每页即时检查 → [对抗审查] 多 Agent 独立审查
    → [记忆持久化] 保存新发现 → 交付
```

### 1.1 核心模块

| 模块 | 职责 | 对应传统环节 |
|------|------|------------|
| **Interrogation Engine** | 结构化拷打，挖掘真实需求 | 替代简单的"Phase 1 需求确认" |
| **Plan Manager** | 生成可交互、可修改的执行计划 | 替代静态的"Phase 3 页面规划" |
| **Memory System** | 跨会话累积用户偏好、错误、洞察 | 全新能力 |
| **Reflection Engine** | 生成中即时反思，避免重复错误 | 替代被动的"Phase 5-6 审查修复" |
| **Adversarial Review** | 多 Agent 独立审查，发现盲点 | 全新能力 |

### 1.2 与执行层的关系

```
[本 skill: orchestrator]
    ├── 拷打引擎 → 输出: 深度需求理解文档
    ├── 计划管理 → 输出: 可交互的 PPT 制作计划
    ├── 记忆系统 → 输出: 注入用户偏好和过往教训的上下文
    └── 对抗审查 → 输出: 审查报告和改进建议
              ↓
[code-to-ppt: executor]
    ├── Phase 2: 配色方案（使用记忆系统中的偏好）
    ├── Phase 3-4: 页面规划与代码生成（基于计划的输出）
    ├── Phase 5-6: 视觉审查与修复（受即时反思指导）
    └── Phase 7: 最终交付
              ↓
[本 skill: 后置处理]
    ├── 即时反思 → 记录本次错误和洞察
    └── 记忆持久化 → 保存到用户档案
```

---

## 2. Interrogation Engine（拷打引擎）

### 2.1 核心原则

**不是"问问题"，而是"挖真相"**。

用户说"我要一个答辩PPT"时，真正需要挖掘的是：
- **情绪真相**：TA 最担心评委问什么问题？
- **认知真相**：TA 认为的核心创新，真的是创新吗？
- **场景真相**：答辩时长？评委人数？是否有提问环节？
- **视觉真相**：TA 有审美偏好但表达不出来

### 2.2 拷打维度（PPT 特化）

| 维度 | 目标 | 拷打策略 |
|------|------|----------|
| **用途与场景** | 确定信息密度和论证深度 | 不是问"什么用途"，而是问"如果只有3分钟，你必须让听众记住什么？" |
| **受众画像** | 确定技术深度和背景说明 | 不是问"给谁看"，而是问"听众中一定有一个人会反对你，他会怎么质疑？" |
| **核心信息** | 提炼主线，避免信息散 | 不是问"内容是什么"，而是问"如果删掉80%的内容，保留哪20%？" |
| **数据与证据** | 确定 hero 面板和图表 | 不是问"有什么数据"，而是问"哪个数字如果放大到全屏，最能说服人？" |
| **视觉约束** | 确定配色和风格来源 | 不是问"有什么要求"，而是问"你有没有见过一个PPT觉得'这就是我想要的'？" |
| **时间限制** | 确定页数和节奏 | 不是问"多少页"，而是问"你讲完一页平均花多久？有没有必须重点讲的页？" |
| **竞品参照** | 确定差异化定位 | 不是问"要什么风格"，而是问"你最不想让你的PPT看起来像什么？" |
| **风险预判** | 提前暴露潜在问题 | 不是问"有什么担心"，而是问"如果答辩后评委说'这个工作没什么新意'，你会怎么反驳？" |

### 2.3 决策树机制

拷打不是清单式提问，而是**决策树**：

```
用途?
├── 学术答辩
│   ├── 学位类型?
│   │   ├── 本科 → 强调工作量、系统性
│   │   ├── 硕士 → 强调创新点、对比实验
│   │   └── 博士 → 强调理论深度、学术贡献
│   ├── 评委构成?
│   │   ├── 校内专家 → 可深入技术细节
│   │   └── 校外专家 → 需更多背景铺垫
│   └── 最可能被质疑的点? → 针对性准备防御页
│
└── 商业路演
    ├── 融资阶段?
    │   ├── 种子轮 → 强调问题存在、市场规模
    │   ├── A轮 → 强调产品验证、增长数据
    │   └── B轮+ → 强调商业模式、护城河
    ├── 听众角色?
    │   ├── 技术投资人 → 可深入架构
    │   └── 财务投资人 → 强调数字和回报
    └── 竞品情况? → 准备差异化对比页
```

每个节点的回答会**解锁新的子问题**，直到达到足够深度。

### 2.4 拷打终止条件

拷打不是无限进行的，终止条件（满足任一）：

1. **信息饱和度**：连续 3 轮提问没有获得新的有效信息
2. **用户疲劳信号**：用户开始用"随便"、"你定"、"就这样吧"回应
3. **关键决策完备**：以下 7 个核心决策都有明确答案：
   - 核心信息（1句话）
   - 受众画像（1个人物描述）
   - 关键数据（1-3个数字）
   - 视觉基调（1个参照物）
   - 页数限制（数字）
   - 时间限制（数字）
   - 最大风险（1个场景）

### 2.5 输出：深度需求理解文档

拷打完成后，生成结构化文档：

```json
{
  "interrogation_summary": {
    "core_message": "一句话核心信息",
    "audience_persona": "听众画像描述",
    "key_data": ["数字1", "数字2"],
    "visual_reference": "视觉参照物描述",
    "page_limit": 10,
    "time_limit_minutes": 15,
    "biggest_risk": "最大风险场景"
  },
  "decision_tree_path": ["用途:学术答辩", "学位:硕士", "评委:校外专家", ...],
  "unresolved_questions": ["用户未明确但可能影响设计的点"],
  "assumptions_made": ["AI 做出的假设（需用户确认）"],
  "confidence_score": 0.85
}
```

---

## 3. Plan Manager（计划管理器）

### 3.1 核心原则

**不是"给计划"，而是"共建计划"**。

传统计划是静态的、一次性的。本模块生成的计划是：
- **可修改**：用户可以直接编辑任何步骤
- **可勾选**：每步有完成状态，跟踪进度
- **可注释**：每步可以添加备注和修改记录
- **可进化**：执行中发现新信息时，计划自动调整

### 3.2 计划结构

计划不是简单的 todo list，而是**有依赖关系的任务图**：

```json
{
  "plan_id": "plan_20260629_001",
  "version": 1,
  "status": "draft|active|completed|abandoned",
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
          "dependencies": [],
          "estimated_minutes": 5,
          "details": "基于拷打结果中的 visual_reference 和用途，设计主色/辅色/中性色/功能色",
          "checkpoint": "向用户展示色板，获得确认",
          "modifiable": true,
          "notes": ""
        },
        {
          "task_id": "p1-t2",
          "task_name": "确定字体层级",
          "status": "pending",
          "dependencies": ["p1-t1"],
          "estimated_minutes": 3,
          "details": "确定封面/标题/正文/Hero/页脚的字号和字体",
          "checkpoint": "与色板一起展示",
          "modifiable": true,
          "notes": ""
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
          "dependencies": [],
          "estimated_minutes": 10,
          "details": "基于拷打结果中的 core_message，设计整份PPT的信息流",
          "checkpoint": "向用户展示故事线大纲，获得确认",
          "modifiable": true,
          "notes": ""
        }
      ]
    }
  ],
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "cover",
      "layout": "cover",
      "title": "...",
      "content_summary": "...",
      "status": "planned|generating|reviewing|completed",
      "task_id": "p3-t1",
      "dependencies": ["p1-t1", "p1-t2", "p2-t1"],
      "notes": ""
    }
  ]
}
```

### 3.3 计划的可修改性

用户可以通过以下方式修改计划：

1. **直接编辑**：修改任何字段（标题、内容、布局）
2. **添加/删除步骤**：插入新任务或删除不需要的任务
3. **调整顺序**：拖拽改变任务或幻灯片的顺序
4. **添加备注**：在任何步骤添加备注，记录决策原因
5. **标记风险**：标记某步骤为高风险，触发额外审查

每次修改后，**依赖关系自动更新**，冲突自动检测。

### 3.4 计划的进化机制

执行过程中，计划会自动进化：

```
生成第3页时发现文字溢出
    ↓
反思引擎记录："3页文字溢出，需要拆分为2页"
    ↓
计划自动调整：
  - 插入新幻灯片（3b）
  - 更新后续页码
  - 添加备注："因内容密度调整，拆分原第3页"
    ↓
向用户报告："发现第3页内容过多，已自动拆分为两页，请确认"
```

---

## 4. Memory System（记忆系统）

### 4.1 核心原则

**不是"记录历史"，而是"积累智慧"**。

记忆系统的目标：让每次新的 PPT 制作都比上一次更懂用户。

### 4.2 三层记忆结构

#### Layer 1: User Profile（用户画像）

跨项目、跨会话累积的**稳定偏好**：

```json
{
  "user_profile": {
    "identity": {
      "institution": "清华大学",
      "department": "计算机系",
      "role": "博士生"
    },
    "design_dna": {
      "preferred_themes": ["academic", "medical"],
      "color_temperature": "cool",
      "density_preference": "high",
      "layout_biases": ["two_column_compare", "hero_panel", "timeline"],
      "font_preferences": {
        "chinese": "Microsoft YaHei",
        "english": "Arial"
      }
    },
    "content_patterns": {
      "common_sections": ["引言", "方法", "实验", "结论"],
      "typical_metrics": ["准确率", "F1分数", "推理速度"],
      "frequent_comparisons": ["U-Net", "ResNet", "Transformer"]
    },
    "communication_style": {
      "response_speed": "fast",  // fast/medium/thorough
      "detail_level": "high",    // high/medium/low
      "correction_tolerance": "medium"  // 用户接受AI自行修正的程度
    }
  }
}
```

**提取方式**：
- 手动：用户主动设置
- 自动：从拷打对话中提取（"你上次说喜欢冷色调"）
- 推断：从执行选择中推断（用户连续3次选择medical主题→偏好medical）

#### Layer 2: Error Registry（错误登记册）

记录**执行中发现的问题及根因**：

```json
{
  "error_registry": [
    {
      "error_id": "err_001",
      "timestamp": "2026-06-29",
      "session_id": "ses_xxx",
      "error_type": "text_overflow",
      "severity": "high",
      "description": "第3页卡片文字溢出边界",
      "root_cause": "h_card 计算未考虑自动换行，实际6行但按5行计算",
      "prevention": "使用 DesignContract.validate_before_build() 强制检查文本容量",
      "affected_slides": [3],
      "fix_applied": "增大 h_card 从 1.7 到 1.9",
      "status": "resolved",
      "lessons_learned": "混合文本（中英文）的行数估算需要更保守"
    },
    {
      "error_id": "err_002",
      "timestamp": "2026-06-29",
      "error_type": "color_inconsistency",
      "severity": "medium",
      "description": "第5页强调线颜色与色板不一致",
      "root_cause": "LLM 在生成时忘记查询 DesignContract 的颜色映射",
      "prevention": "在 prompt 中强制注入 DesignContract 上下文摘要",
      "affected_slides": [5],
      "fix_applied": "统一为 semantic_colors.warning = #C0392B",
      "status": "resolved",
      "lessons_learned": "上下文注入对长程一致性至关重要"
    }
  ]
}
```

**使用方式**：
- 新会话开始时，加载相关错误，提醒 LLM"上次你在这里犯过错"
- 执行中，遇到相似场景时主动告警
- 定期生成"错误模式报告"，发现系统性问题

#### Layer 3: Insight Cache（洞察缓存）

记录**后期发现的有价值的洞察**：

```json
{
  "insight_cache": [
    {
      "insight_id": "ins_001",
      "timestamp": "2026-06-29",
      "session_id": "ses_xxx",
      "insight": "答辩PPT的实验结果页使用 hero_panel + 双栏对比的组合布局，效果最佳",
      "trigger": "用户反馈'数据不够突出'，修改后用户满意",
      "confidence": 0.9,
      "application_scope": "academic_defense, experiment_result_pages",
      "prerequisites": ["有1-3个关键指标", "有对比实验数据"]
    },
    {
      "insight_id": "ins_002",
      "timestamp": "2026-06-29",
      "session_id": "ses_xxx",
      "insight": "对于校外专家评委，方法页需要增加更多背景铺垫，不能太跳跃",
      "trigger": "拷打时发现用户担心'评委不是这个领域的'",
      "confidence": 0.85,
      "application_scope": "academic_defense, method_pages, external_reviewers",
      "prerequisites": ["评委包含校外专家"]
    }
  ]
}
```

**使用方式**：
- 新会话开始时，根据当前场景匹配相关洞察，注入 prompt
- 执行中，遇到匹配场景时主动建议
- 定期清理低置信度或过时的洞察

### 4.3 记忆持久化

**存储位置**：`~/.config/code-to-ppt/memory/{user_id}.json`

**加载时机**：
1. **会话开始时**：加载 User Profile，注入拷打引擎 prompt
2. **计划生成时**：加载 Error Registry，标记需要特别注意的步骤
3. **执行开始时**：加载 Insight Cache，注入 DesignContract 上下文

**保存时机**：
1. **会话结束时**：保存所有新发现
2. **用户显式触发**："/save-memory" 命令
3. **自动保存**：每完成一页后自动增量保存

---

## 5. Reflection Engine（反思引擎）

### 5.1 核心原则

**不是"事后总结"，而是"即时修正"**。

反思发生在三个时机：

| 时机 | 触发条件 | 反思内容 |
|------|----------|----------|
| **Per-Slide Reflection** | 每生成一页后 | 检查这页是否符合用户偏好、是否有已知错误模式 |
| **Phase Reflection** | 每完成一个 Phase 后 | 检查阶段性产出是否偏离计划、是否需要调整后续计划 |
| **Post-Session Reflection** | 会话结束时 | 总结本次新发现、更新记忆系统、生成改进建议 |

### 5.2 Per-Slide Reflection 检查清单

每生成一页后，自动运行以下检查：

```markdown
## Slide Reflection Checklist (Page N)

### 内容检查
- [ ] 是否超过 8 行 bullet？
- [ ] 是否有具体数据（非纯定性描述）？
- [ ] 核心信息是否在一句话内可概括？

### 视觉检查
- [ ] 布局是否与拷打结果中的 visual_reference 一致？
- [ ] 强调线颜色是否符合语义（positive=绿, warning=红, contrast=金）？
- [ ] 是否存在左侧竖线装饰（反 AI 味）？
- [ ] 页脚是否为短线（~1.8"）？

### 一致性检查
- [ ] 与前页的过渡是否自然？
- [ ] 字体、字号是否遵循 DesignContract？
- [ ] 颜色是否与色板一致？

### 记忆检查
- [ ] 是否触发了 Error Registry 中的已知错误模式？
- [ ] 是否可应用 Insight Cache 中的任何洞察？
- [ ] 是否符合 User Profile 中的偏好？

### 节奏检查
- [ ] 是否已连续 2 页同布局？（如果是，告警）
- [ ] 距上次 hero_panel 是否 ≥2 页？（如果不足，告警）
```

### 5.3 反思驱动的自动修正

当检查发现问题时，**自动修正**而非仅告警：

```
检查：第5页 bullet 数量 = 10
    ↓
触发：超过上限 8
    ↓
自动修正：
  1. 将最后 2 个 bullet 移到新页（5b）
  2. 更新计划，插入新幻灯片
  3. 向用户报告："第5页内容过多，已自动拆分为两页"
```

### 5.4 Post-Session Reflection 报告

会话结束时生成：

```markdown
## Session Reflection Report

### 执行摘要
- 总页数：12
- 生成时间：25 分钟
- 修改轮次：3

### 新发现
1. **布局模式**：用户对 timeline 布局的接受度高于预期，下次可多用
2. **配色偏好**：用户主动要求加深主色饱和度，记录到 User Profile

### 错误记录
1. **text_overflow** (Page 3)：已记录到 Error Registry
2. **image_misalignment** (Page 7)：已记录到 Error Registry

### 洞察积累
1. **洞察 #3**：对于 15 分钟答辩，10-12 页是最佳长度
2. **洞察 #4**：封面使用机构 Logo 时，需要预留 0.5" 安全边距

### 改进建议
1. 下次拷打时应主动询问"是否有必须展示的机构 Logo"
2. 考虑增加"答辩时长 vs 页数"的自动推荐功能

### 记忆更新
- User Profile：更新 color_temperature 为 "cool-high-saturation"
- Error Registry：新增 2 条记录
- Insight Cache：新增 2 条记录
```

---

## 6. Adversarial Review（对抗审查）

### 6.1 核心原则

**不是"自己审查自己"，而是"让独立专家挑刺"**。

对抗审查的关键：**独立性**。审查 Agent 不能看到主 Agent 的思考过程，只能看到最终产出。

### 6.2 三 Agent 审查体系

#### Agent A: Creative Reviewer（创意审查）

**角色**：视觉设计师 + 创意总监
**审查维度**：
- 这页够吸引人吗？第一眼能看到重点吗？
- 布局是否太保守？有没有更有趣的呈现方式？
- 颜色搭配是否平庸？有没有更出彩的方案？
- 信息层级是否清晰？视线流动是否自然？

**输出**：
```json
{
  "reviewer": "Creative",
  "score": 7.5,
  "findings": [
    {
      "severity": "high",
      "issue": "第3页左右对比布局太常见，建议改用上下渐变对比",
      "suggestion": "上半屏放基线方法（灰度），下半屏放本文方法（彩色），中间用动画箭头连接"
    }
  ]
}
```

#### Agent B: Logic Reviewer（逻辑审查）

**角色**：逻辑学家 + 内容策略师
**审查维度**：
- 论证链条是否完整？有没有跳跃？
- 数据是否支撑结论？有没有过度解读？
- 信息密度是否合理？听众能跟上吗？
- 故事线是否连贯？每页是否有明确的过渡？

**输出**：
```json
{
  "reviewer": "Logic",
  "score": 8.0,
  "findings": [
    {
      "severity": "medium",
      "issue": "第5页从'方法'跳到'实验'，缺少'实验设置'的过渡",
      "suggestion": "增加一页'实验设置'，说明数据集、评价指标、对比方法"
    }
  ]
}
```

#### Agent C: Execution Reviewer（执行审查）

**角色**：项目经理 + 技术审核
**审查维度**：
- 计划在时间内可完成吗？
- 是否有技术风险（如图片缺失、字体不兼容）？
- 资源是否充足（图片素材、数据文件）？
- 交付物是否符合要求（格式、分辨率、大小）？

**输出**：
```json
{
  "reviewer": "Execution",
  "score": 6.5,
  "findings": [
    {
      "severity": "high",
      "issue": "第7页引用的图片 'fig3.png' 在素材目录中不存在",
      "suggestion": "立即确认图片路径，或生成占位符并提醒用户"
    }
  ]
}
```

### 6.3 审查触发时机

| 时机 | 审查对象 | 审查深度 |
|------|----------|----------|
**计划审查** | 完整计划文档 | 三 Agent 全面审查 |
| **Checkpoint 审查** | 最近 3 页 | 快速审查（重点：一致性、节奏） |
| **最终审查** | 完整 deck | 三 Agent 全面审查 + 交叉验证 |

### 6.4 综合裁决

主 Agent 汇总三方意见，给出最终建议：

```markdown
## Adversarial Review Summary

### 创意审查 (Score: 7.5)
- **关键发现**：第3页布局太常见
- **建议**：改用上下渐变对比
- **采纳**：是。修改计划，更新第3页布局。

### 逻辑审查 (Score: 8.0)
- **关键发现**：方法到实验缺少过渡
- **建议**：增加"实验设置"页
- **采纳**：是。在计划中添加新页。

### 执行审查 (Score: 6.5)
- **关键发现**：第7页图片缺失
- **建议**：确认图片路径
- **采纳**：是。暂停生成，向用户确认。

### 综合决策
1. **立即执行**：修改第3页布局、添加实验设置页
2. **阻塞等待**：确认 fig3.png 路径
3. **风险评级**：中等（图片问题可能导致延误）
```

---

## 7. 完整工作流

### 7.1 会话启动流程

```
用户: "帮我做一个答辩PPT"
    ↓
[记忆加载]
  → 加载 User Profile
  → 加载相关 Error Registry（上次答辩的错误）
  → 加载相关 Insight Cache（答辩相关的洞察）
    ↓
[拷打引擎]
  → 基于记忆，提出精准问题
  → 挖掘真实需求
  → 生成深度需求理解文档
    ↓
[计划管理器]
  → 基于需求和记忆，生成初始计划
  → 向用户展示，获得确认/修改
    ↓
[对抗审查 - 计划审查]
  → 三 Agent 独立审查计划
  → 综合裁决，修改计划
    ↓
用户确认计划
    ↓
[执行层执行]
```

### 7.2 单页生成流程

```
[计划管理器] 获取下一页任务
    ↓
[记忆注入]
  → 注入 User Profile（配色偏好）
  → 注入相关 Error Registry（避免重复错误）
  → 注入相关 Insight Cache（应用过往洞察）
    ↓
[DesignContract] 加载当前设计契约
    ↓
[执行层] 生成单页代码
    ↓
[自优化闭环]
  → 运行脚本 → 导出 PNG → 视觉审查 → 修复
    ↓
[反思引擎 - Per-Slide Reflection]
  → 运行检查清单
  → 自动修正或告警
    ↓
每3页后：[对抗审查 - Checkpoint 审查]
    ↓
全部完成后：[对抗审查 - 最终审查]
    ↓
[反思引擎 - Post-Session Reflection]
  → 生成反思报告
    ↓
[记忆持久化]
  → 保存 User Profile 更新
  → 保存新错误到 Error Registry
  → 保存新洞察到 Insight Cache
    ↓
交付
```

### 7.3 用户交互命令

| 命令 | 功能 |
|------|------|
| `/interrogate` | 手动触发拷打引擎 |
| `/plan` | 查看/修改当前计划 |
| `/memory` | 查看记忆系统内容 |
| `/reflect` | 手动触发反思 |
| `/review` | 手动触发对抗审查 |
| `/save-memory` | 手动保存记忆 |
| `/load-memory` | 加载特定记忆文件 |

---

## 8. 内部模块集成点

### 8.1 Orchestrator → Executor

Orchestrator 向执行层（SKILL.md 定义的 code-to-ppt 工作流）提供以下输入：

1. **拷打结果**：`interrogation_summary.json`
   - Phase 1 直接使用，无需再次询问

2. **计划文档**：`plan.json`
   - Phase 3 直接使用，包含每页的布局、内容、顺序

3. **记忆上下文**：`memory_context.json`
   - Phase 2（配色）使用 User Profile 的偏好
   - Phase 4-6 使用 Error Registry 和 Insight Cache

4. **设计契约**：`design_contract.json`
   - 所有 Phase 使用，保证长程一致性

### 8.2 Executor → Orchestrator

执行层向 Orchestrator 提供以下输出：

1. **执行日志**：`execution_log.json`
   - 即时反思分析执行日志，发现错误和洞察

2. **最终产出**：`.pptx` 文件 + PNG 截图
   - 对抗审查审查最终产出

3. **用户反馈**：用户显式给出的修改意见
   - 记忆系统提取偏好和洞察

---

## 9. 文件结构

```
code-to-ppt/
├── SKILL.md                          # 本文件
├── SKILL_EN.md                       # 英文版 skill 文档
├── README.md                         # 项目介绍
│
├── src/
│   ├── interrogation_engine.py       # 拷打引擎
│   ├── memory_system.py              # 记忆系统
│   ├── adversarial_review.py         # 对抗审查
│   ├── orchestrator.py               # 主控制器
│   ├── layout_manager.py             # 自动布局分配
│   ├── design_contract.py            # 长程一致性
│   └── dual_track_api.py             # 声明式 + 精确控制 API
│
└── examples/                         # 示例（待补充）
```

---

## 10. 下一步

本 skill 是一个**框架性设计**，需要逐步实现：

1. **P0（核心）**：实现拷打引擎的决策树和 PPT 特化问题模板
2. **P1（核心）**：实现计划管理器的可交互计划结构
3. **P2（增强）**：实现记忆系统的三层结构和持久化
4. **P3（增强）**：实现反思引擎的检查清单和自动修正
5. **P4（差异化）**：实现对抗审查的三 Agent 体系
6. **P5（集成）**：打通 Orchestrator 与执行层的输入输出接口

建议从 **P0 + P1** 开始，先让"拷打 + 计划"跑起来，再逐步叠加记忆、反思、审查。

**本 skill 的终极目标**：让用户说出"我要一个答辩PPT"后，AI 能反问出连用户自己都没想到的关键问题，生成一份比用户自己想的还周全的计划，并且在执行中不断学习和进化，最终产出一份**真正打动听众**的 PPT。
