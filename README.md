<div align="center">

# 🎨 code-to-ppt

#### 自主执行 + 独立 Agent 审查 + 顾问式立场的 PPT 制作 skill

[![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](./LICENSE)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/Platforms-4-D97706?style=for-the-badge)](#-平台兼容)
[![Linux.do](https://shorturl.at/ggSqS)](https://linux.do)
![Claude Code](https://img.shields.io/badge/Claude_Code-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-8B5CF6?style=flat-square)

</div>

---

## 💎 这个 skill 的核心优势

大多数 PPT skill 的流程是：套模板 → 一张张图堆出来 → 导出文件。**问题是被模板绑架**——最后得到的是"看起来还行但没有任何一个观点站得住"的 deck。

code-to-ppt 走的是另一条路：

| 维度 | 别的 PPT skill | code-to-ppt |
|---|---|---|
| **不讨好用户** | 用户说什么就做什么 | 当用户的要求会让 PPT 变差时，主动提出异议 |
| **去 AI 味** | 紫蓝渐变、emoji 满天飞、阴影玻璃滥用 | 明确禁止这些 AI 味设计 |
| **零依赖** | Node.js / Python / 大量代码 | 纯 Markdown + YAML frontmatter，没有 Python 包 |
| **自定义评分** | 固定 4 维度 | 基线 4 维度（25×4=100），用户可以加自定义维度 |
| **辅助而非限制** | 框架约束模型发挥 | 没有用框架限制，而是为模型提供方法论 |
| **开放不绑定** | 模板和设计写死 | 模板和设计都未写死，能和其他 skill 结合使用 |

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

## 🚀 平台兼容

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
阶段 4: 逐页实现 ──→ 自主生成 .pptx（用模型最擅长的方式，具体工具由运行环境决定）
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
- ✅ 想要"可放进作品集"那种质量

- ❌ 临时分享、3-5 页 quick update（太重）
- ❌ 纯视觉炫技型（KPI 大屏、品牌发布）

---

## ⚙️ 核心技术决策

| 决策 | 选择 | 原因 |
|---|---|---|
| **生成方式** | 不绑定具体生成器 | skill 只规定方法论（访谈→架构→设计→实现→审查→迭代），实现层由模型/环境自由选择，可写代码、可用工具链、可调外部服务 |
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

## 💡 解决什么痛点

- 不想花时间做组会 / 报告 PPT
- 担心数据安全（不上传第三方平台）
- 纠结风格设计
- 不清楚 PPT 该怎么做

直接用这个 skill 搞定。

---

## 📜 License

MIT — 自由使用 / 修改 / 再分发

---

<div align="center">

Made by [@ColorsOutofSpace](https://github.com/ColorsOutofSpace)

如果这个 skill 帮到了你，给个 ⭐ 就行。

</div>
