<div align="center">

# 🎨 code-to-ppt

#### 把想法变成有说服力的演示文稿，不是把模板套到空页上

[![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](./LICENSE)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/Platforms-4-D97706?style=for-the-badge)](#-平台兼容)

![Claude Code](https://img.shields.io/badge/Claude_Code-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-8B5CF6?style=flat-square)

</div>

> **"你给方向，AI 设计；确认后 AI 自己完成所有工作，你只在结果上有否决权。"**

---

## 📋 一句话能力卡

| 能力 | 数字 | 位置 |
|---|---|---|
| 🎤 **审查 Agent 角色** | **4** | 目标受众 / 挑剔设计师 / 逻辑审查者 / 时间管理者 |
| 📚 **方法论文件** | **5** | `references/*.md` |
| 🔄 **工作流阶段** | **7** | 访谈 → 架构 → 设计 → 实现 → 审查 → 迭代 → 交付 |
| 📊 **量化评分** | **0-100** | 评审主席汇总 4 份独立报告 |
| 💾 **记忆文件** | **单一文件** | `.code-to-ppt/memory.md`（项目隔离）|
| 📦 **依赖** | **零** | 没有 Python 包、没有 src/、纯 Markdown |

---

## 🤔 它和别的 PPT skill 有什么不同

市面上大多数 PPT skill 的流程是这样的：

```
用户输入 → 大纲模板 → HTML/Marp 渲染 → 一张张图堆出来 → 导出 .pptx
```

这种流程有两个问题：
- **作者被模板绑架**：要套主题、套版式、套动画，最后得到的是"看起来还行但没有任何一个观点站得住"的 deck
- **审查走过场**：单 LLM 自审，倾向给自己高分，无法避免 confirmation bias

code-to-ppt 走的是另一条路：

```
用户输入 → 深度认知访谈（5-12 个问题）→ 风险识别 + 挑战性问题
       → 金字塔叙事架构（结论先行 → 理由 → 证据）
       → 内容驱动视觉设计（配色 / 字体 / 母题）
       → 自主实现（python-pptx 写代码生成）
       → 4 个独立 Agent 审查（隔离 + 不给设计历史）
       → 评审主席汇总 + 量化打分
       → 自主迭代直到 ≥ 80 分
```

**核心卖点**：3 个
- **顾问式立场**：主动发现风险、不迎合用户的"想要"，只服务于"达成目标"
- **独立 Agent 审查**：4 个 LLM 角色在 prompt 层隔离，避免"换面具自审"
- **可协商量化评分**：基线 4 维度（25×4=100），用户可加自定义维度，系统权重自动调整

---

## 🚀 平台兼容

支持所有主流 Skill 标准的 Agent：

| 工具 | 安装目录 | 安装命令 |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | `cp -r code-to-ppt ~/.claude/skills/` |
| **Codex** | `~/.codex/skills/` | `cp -r code-to-ppt ~/.codex/skills/` |
| **OpenCode** | `~/.config/opencode/skills/` | `cp -r code-to-ppt ~/.config/opencode/skills/` |
| **OpenClaw** | `~/.openclaw/skills/` | `cp -r code-to-ppt ~/.openclaw/skills/` |

或一行命令（让 agent 自己装）：

```
帮我安装这个 skill：https://github.com/ColorsOutofSpace/code-to-ppt
```

---

## 📖 使用方式

安装后，对 agent 说：

```
帮我做个答辩 PPT
帮我做个 Q4 总结
帮我做个融资 deck
```

支持任何触发词：**PPT、幻灯片、presentation、答辩、汇报、路演、deck、roadmap**。

### 完整工作流

```
阶段 1: 认知访谈 ──→ 5-12 个问题挖出真实需求（5-10 分钟）
                       ↓
阶段 2: 信息架构 ──→ 金字塔叙事（结论 → 理由 → 证据）
                       ↓
阶段 3: 视觉设计 ──→ 内容驱动配色、字体、母题
                       ↓
阶段 4: 逐页实现 ──→ 自主生成 .pptx（python-pptx 写代码）
                       ↓
阶段 5: 对抗审查 ──→ 4 个独立 Agent 隔离审查
                       ↓
阶段 6: 反思迭代 ──→ 自主修复 High 问题，量化评分 ≥ 80 才停
                       ↓
阶段 7: 交付
```

**只有阶段 1 需要你深度参与**。从阶段 2 开始 AI 自主推进，你随时可以"停/改/等等"打断。

---

## 📂 项目结构

```
code-to-ppt/
├── SKILL.md                          # LLM 主入口：触发 + 主线流程 + references 路由
├── README.md                         # 本文件
├── LICENSE                           # MIT
└── references/                       # 方法论参考文件
    ├── 01_interrogation.md           # 认知访谈 + 风险识别 + 挑战性问题
    ├── 02_visual_design.md           # 视觉设计系统（dominance 60-30-10、视觉母题、三明治）
    ├── 03a_audience.md               # 独立审查者 1：目标受众
    ├── 03b_design.md                 # 独立审查者 2：挑剔设计师
    ├── 03c_logic.md                  # 独立审查者 3：逻辑审查者
    ├── 03d_time.md                   # 独立审查者 4：时间管理者
    ├── 03_adversarial_review.md      # 评审主席：汇总 4 份独立报告 + 评分
    ├── 04_reflection_loop.md         # 自主迭代循环
    └── 05_customization.md           # 协商审查标准 + 记忆管理
```

---

## 🎯 适用场景

- ✅ 答辩、汇报、融资、路演、季度总结
- ✅ 5-30 页的正式演示文稿
- ✅ 对内容逻辑和视觉一致性都有高要求
- ✅ 想要"可上传到 GitHub、放进作品集"那种质量

- ❌ 临时分享、3-5 页 quick update（太重）
- ❌ 纯视觉炫技型（KPI 大屏、品牌发布）—— 用 `lewislulu/html-ppt-skill` 更合适
- ❌ 图片型 slide（vibe PPT）—— 用 `codex-ppt-skill` 更合适

---

## ⚙️ 核心技术决策

| 决策 | 选择 | 原因 |
|---|---|---|
| **生成方式** | python-pptx 代码生成 | LLM 最自然的方式，可以迭代修复具体问题 |
| **审查机制** | 4 个独立 Agent 角色 + 评审主席 | 避免 confirmation bias |
| **交互模式** | 阶段 1 深度参与，之后自主 | 用户不需要每步确认 |
| **记忆系统** | `.code-to-ppt/memory.md`（项目隔离）| 一个项目一份 memory，5KB 上限防止膨胀 |
| **依赖** | 零（纯 Markdown + YAML frontmatter） | 极简，可移植，无安装成本 |

---

## 📐 设计哲学

### 1. 内容驱动设计
配色、字体、风格不是随机选的，必须反映演示主题和受众。如果把这些配色换到另一个完全不相关的主题上依然"能用"，说明选择不够具体。

### 2. 顾问式立场
用户的愿望 ≠ 用户的利益。当用户的要求会导致演示效果变差时，AI 有责任提出异议并给出替代方案。**核心：服务于"达成演示目标"，不是"满足每个要求"**。

### 3. 独立审查隔离
4 个审查角色在 prompt 层隔离：每个角色只看到 PPT 内容、看不到其他角色的报告、看不到设计决策历史。**这在最大程度上减少 confirmation bias**。

### 4. 记忆约束
单个 memory 文件 ≤ 5KB。超限时按主题自动合并为长期配置，每个主题只保留最近 3 条摘要。**避免长期使用后 memory 膨胀失控**。

### 5. 项目隔离
每个项目独立一份 `.code-to-ppt/memory.md`，无需 user_id。**上下文窗口干净**。

---

## 🔗 相关项目

- [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) — 数字生命卡兹克的 AI Skills 合集
- [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) — 36 套主题的 HTML PPT Studio
- [codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) — 整页图片式 PPT 生成
- [Mr-Q526/PPTMaker-skill](https://github.com/Mr-Q526/PPTMaker-skill) — 结构化 deck.json 工作流

---

## 📜 License

MIT — 自由使用 / 修改 / 再分发

---

<div align="center">

Made by [@ColorsOutofSpace](https://github.com/ColorsOutofSpace)

如果这个 skill 帮到了你，给个 ⭐ 就行。

</div>
