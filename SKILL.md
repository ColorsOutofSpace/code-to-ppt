---
name: code-to-ppt
description: Use when the user asks to generate a .pptx presentation using Python code. Implements a self-optimization loop — python-pptx generation → PNG export → MCP vision review → code fix → regenerate. Covers anti-AI-flavor design patterns, layout variety, and visual QA. Includes cognitive enhancement layer (interrogation, memory, adversarial review) where Python returns prompt packages for the LLM tool to execute. Suitable for any presentation purpose; color scheme is chosen based on the user's specific use case.
---

# code-to-ppt：认知增强型 PPT 制作 skill

## 1. Overview

本 skill 是一个**认知增强型 PPT 制作系统**，包含两层：

1. **认知层**（src/orchestrator.py + 6 个引擎模块）：负责需求挖掘、记忆管理、计划生成、对抗审查、反思
2. **执行层**（python-pptx + helper 函数 + 6-Phase 工作流）：负责实际代码生成

**关键设计**：Python 端不直接调 LLM。每个 orchestrator 方法返回 **prompt 包**（dict），LLM 工具（Claude Code / Codex 等）读 prompt 后自己执行智能行为（问用户、写代码、审查）。

```
LLM 工具调用 orchestrator.xxx() → 拿到 prompt 包 → 读 prompt 自己执行 → 把结果传回 orchestrator 聚合
```

核心创新：**打通「拷打引擎 → 计划管理 → 记忆注入 → python-pptx 生成 → 即时反思 → 对抗审查 → 记忆持久化」的自优化闭环**。不同于一次性生成图片或套用模板的工具，本 skill 产出的文件是原生可编辑的 .pptx，且会经过拷打挖掘真实需求 + 视觉审查 → 修复的迭代循环来保证最终质量。

不限 PPT 用途——答辩、汇报、路演、课程报告等均可，配色方案会根据具体场景自主设计。

## 2. When to Use

以下任一情况应加载本 skill：

- 用户要求生成 `.pptx` 文件
- 用户要求制作幻灯片 / PPT / 演示文稿
- 用户要求修改已有的 PPT 生成代码
- 用户提到 `python-pptx`

## 3. 自优化闭环工作流

严格按以下 6 个 Phase 执行。**Phase 1 是强制步骤，禁止跳过。**

```
Phase 1: 需求确认 ──→ Phase 2: 配色方案 ──→ Phase 3: 页面规划
                                                    │
                                                    ▼
Phase 6: 最终交付 ←── Phase 5: 修复验证 ←── Phase 4: 视觉审查
                                                    │
                                    (PPTX → PNG → MCP 图片理解)
```

---

### Phase 1: 需求确认（MANDATORY）

**在编写任何代码之前**，必须先通过拷打引擎挖出真实需求。**不要直接问用户"你要什么 PPT"**——通过决策树逐层深入。

#### 1.1 启动拷打会话

```python
from src.orchestrator import create_orchestrator
orch = create_orchestrator(user_id="user_123")
orch.start_session(topic, deck_type="thesis")  # deck_type 决定 design_contract 主题
ctx = orch.start_interrogation(user_initial_input)
```

`ctx["current_node"]` 包含当前要问的问题、选项、is_critical 标记。

#### 1.2 推进决策树

读 `ctx["current_node"]["question"]`，向用户提问，记录回答，调 `orch.advance_interrogation(ctx, answer)` 推进。

终止条件（任一满足）：
- `ctx["status"] == "completed"`：决策树走完
- `ctx["status"] == "needs_user_fatigue_check"`：连续 3 轮无新信息，询问用户是否继续
- LLM 判断关键决策已完备 → 调 `orch.force_complete_interrogation(ctx)` 强制结束

#### 1.3 关键决策完备性检查

拷打应至少覆盖以下 6 个核心决策：
- 核心信息（core_message）
- 受众画像（audience_persona）
- 关键数据（key_data）
- 视觉参照（visual_reference）
- 时间/页数限制
- 最大风险（biggest_risk）

---

### Phase 2: 配色方案选择

**核心原则：不写死颜色。DesignContract 在 start_session 时按 deck_type 自动初始化主题。**

`orch.design_contract` 在 `start_session(deck_type=...)` 时自动初始化：

| deck_type | 主题 | 适用场景 |
|----------|------|----------|
| `thesis` / `academic` / `research` | ACADEMIC | 学术答辩、研究汇报 |
| `pitch` / `business` / `report` | BUSINESS | 商业路演、工作汇报 |
| `medical` / `healthcare` | MEDICAL | 医疗、医学相关 |
| `tech` / `technology` | TECH | 技术、产品发布 |
| `creative` / `design` | CREATIVE | 创意、设计汇报 |
| 其他 | ACADEMIC（默认） | — |

决策维度（LLM 可在生成的代码中微调）：
- **受众** → 对比度：正式场合强对比（深底白字），内部汇报可弱对比（浅底深字）
- **机构/品牌** → 主色来源：如有 Logo 或 VI 色，优先沿用

**4 层色板**（已预定义在 DesignContract，每层 2-4 个色）：

| 层级 | 数量 | 用途 |
|------|------|------|
| 主色 | 1-2 个 | 封面背景、章节过渡页、页面标题 |
| 辅色 | 2-3 个 | 卡片顶部强调线、图表主色调 |
| 中性色 | 3-4 个 | 正文黑 `#1A1A1A`、灰色 `#6B7B8D`、浅底 `#EDF2F8`、白 `#FFFFFF` |
| 功能色 | 3-4 个 | 正面/增长=绿，警告/局限=红/橙，对比/背景=金 |

卡片顶部强调线颜色按语义映射：
- 通用内容 → 辅色
- 核心创新/贡献/收益 → 功能色-正面（绿）或主色加亮
- 对比/已有研究/背景 → 功能色-对比（金/橙）
- 局限/问题/代价 → 功能色-警告（红）

在生成代码时，调 `orch.execute_slide(slide_config)` 拿到 `design_contract` 字段，**严格按该色板生成代码**。

---

### Phase 3: 页面结构规划

1. 按逻辑将内容分组，确定每页主题
2. 页面类型分布：封面 → 大纲 → 内容页（N 页）→ 总结 → 致谢
3. 标注每页类型：纯排版页 / 图片页 / 混合页
4. 每页预计不超过 8 行文字（不含页脚和章节标签）
5. 如有章节过渡需求，在大段落之间插入章节过渡页

**规划完成后，将大纲展示给用户确认，确认后再进入 Phase 4。**

---

### Phase 4: 代码编写

#### 4.1 搭建基础设施

1. 根据 Phase 2 的色板，定义 `RGBColor` 颜色常量
2. 在生成的 python-pptx 脚本中**自己实现** helper 函数（`tx`、`cd`、`plot_card`、`img_fit`、`band`、`hero`、`ft`、`st`、`sT` 等），LLM 工具按需生成
3. 设置图片路径 `FIG` 和输出路径 `OUT`
4. 修改 `ft()` 中的机构名称为 Phase 1 确认的值

#### 4.2 逐页精确布局计算（写代码前必做）

**每页在写代码之前，必须完成以下 4 步计算。禁止凭感觉估计。**

**Step A: 垂直空间预算**

幻灯片有效区域：
- 头部（`st` + `sT`）：y=0 到 y≈0.95，固定占用约 0.95"
- 脚部（`ft` 页脚线）：y=5.25 到 y=5.625，固定占用约 0.375"
- **可用内容高度：5.25 − 0.95 = 4.3"**（从 y≈1.0 到 y≈5.2）

对当前页列出所有元素的 y 坐标和高度，求和 ≤ 4.3"。剩余空间均匀分配或转化为元素间间隙，绝不能堆在底部。

```
示例——双卡片页的垂直预算：
  st+sT           0.00 – 0.95  (固定)
  cd(card1)       1.05 – 2.75  (h=1.7)
  gap             2.75 – 2.90  (h=0.15)
  cd(card2)       2.90 – 4.60  (h=1.7)
  gap             4.60 – 4.85  (h=0.25)
  ft              5.25 – 5.625 (固定)
  内容总计: 1.7+0.15+1.7+0.25 = 3.8" ≤ 4.3" ✓, 剩余 0.5" 均匀分配到 gap
```

**Step B: 文本实际行数估算（最容易出错的环节）**

`cd()` body 文本在宽度 `(w − 0.28)` 英寸内排版。以 9.5pt 微软雅黑为例：
- 中文字符近似宽度 ≈ 9.5/72 ≈ 0.132"
- 英文/数字近似宽度 ≈ 0.066"（中文字符的一半）
- 每行容纳中文字符数 ≈ `(w − 0.28) / 0.132`
- 混合文本取等效字符数：1 个中文 = 1 个等效字符，1 个英文/数字 = 0.5 个等效字符

**实际渲染行数** = Σ ceil(该逻辑行的等效字符数 / 每行容纳中文字符数)，其中逻辑行 = `text.split('\n')`

> 详细公式和常见卡片宽度的行数速查表见下文「文本换行行数估算」小节。

**Step C: cd() 高度反推**

```
所需 h_card = 0.42 + (实际渲染行数 × fs × ls / 72) + 0.05(安全余量)
```

`cd()` 默认 `fs=9.5, ls=1.45` → 每行占用 `9.5 × 1.45 / 72 = 0.191"`

| 实际行数 | 最小 h_card | 建议 h_card |
|----------|------------|------------|
| 2 | 0.87" | 1.0" |
| 3 | 1.06" | 1.2" |
| 4 | 1.25" | 1.4" |
| 5 | 1.44" | 1.6" |
| 6 | 1.63" | 1.8" |
| 7 | 1.83" | 2.0" |
| 8 | 2.02" | 2.2" |

如果反推的 `h_card` 放不进页面空间预算，优先缩减文字（删冗余修饰），其次才扩大卡片。

**Step D: 剩余空间分配**

若 `sum(内容元素高度 + 间隙) < 4.3"`：
1. **差额 < 0.3"** → 均匀增加到各 gap
2. **差额 0.3"–0.8"** → 按比例分配给各卡片/图片增加高度
3. **差额 > 0.8"** → 考虑增加一个 `band()` 色带或 `hero()` 统计模块，让页面充实

**Step E: 写代码**

每页代码前加注释标注验算结果（这是给自己看的，便于 debug）：

```python
# === S7: 数据集概况 ===
# 垂直: st+sT(0.95) + cd(1.7) + gap(0.15) + plot_card(1.7) + ft(0.375) = 4.875 ✓
# cd body w=4.12": 四个逻辑行→实际5行→需 h≥1.43, h_card=1.7 ✓
```

- 图片页优先用 `plot_card()`，文字页用 `cd()`
- 混合布局（上图下析 / 左图右文）按 Step A 预算分配高度
- 每页以 `ft(sl, 页码)` 收尾
- 每页后加 `print("S7")` 便于定位运行错误

#### 4.3 遵循设计原则

- 见第 5 节「设计指导」

---

### Phase 5: 视觉审查

这是本 skill 区别于其他 PPT skill 的核心步骤。

1. **生成 PPTX**：运行 python 脚本
2. **导出 PNG**：
   - Windows：用 PowerPoint COM 自动化导出每页为 PNG（1920×1080）
   - Linux/Mac：用 LibreOffice 命令行导出
3. **逐页审查**：使用 MCP 图片理解工具（如 `mcp__MiniMax__understand_image`）检查每页：
   - 文字是否溢出卡片边界
   - 图片是否变形（宽高比不正确）
   - 元素是否重叠或遮挡
   - 字号是否过小（< 7pt 不可接受）
   - 配色是否一致，是否符合 Phase 2 定义的色板
4. **记录问题**：页号 + 具体元素 + 问题描述

逐页审查的 prompt 模板：
```
Check this PPT slide for:
1. Text overflow — any text touching or exceeding card/box borders
2. Image distortion — wrong aspect ratio
3. Element overlap — shapes or text overlapping each other
4. Font too small — text below 7pt
5. Color consistency — colors match the defined palette
Report only problems found. Say "no problems" if clean.
```

---

### Phase 6: 修复验证 + 最终交付

1. 逐条修复 Phase 5 发现的问题
2. 仅重新导出受影响页面的 PNG，再次审查
3. 循环修复和审查直到所有页面通过
4. 输出完整 `.pptx` 文件
5. 向用户汇报：总页数、图片数、关键数据点

---

## 4. 基础设施：Helper 函数体系

> 以下为速查表（LLM 工具按需生成完整代码实现）。

python-pptx 操作单位为英寸（Inches）。16:9 = 10 × 5.625"。

| 函数 | 用途 | 关键参数 |
|------|------|----------|
| `get_img_size(name)` | PIL 预读图片像素尺寸，缓存结果 | `name`: 相对于 FIG 的文件名 |
| `img_fit(sl, name, l, t, max_w, max_h, align)` | 等比缩放放置图片，缺失时红色占位 | `align`: "center"/"left"/"right" |
| `tx(sl, l, t, w, h, text, **kw)` | 单段文本，必须设置 `eaTypeface` | `fs`, `cl`, `bd`, `ls` |
| `ri(sl, l, t, w, h, runs)` | 多段混合格式文本 | `runs`: [(text, {kw}), ...] |
| `bu(sl, l, t, w, h, items)` | 项目符号列表 | 蓝色圆点自动添加 |
| `cd(sl, l, t, w, h, title, body, accent)` | 内容卡片：白底 + 顶部强调线 + 标题 + 正文 | `accent`: 强调线颜色（语义化） |
| `plot_card(sl, l, t, w, h, name, title, accent)` | 图片卡片：白底 + 强调线 + 图片 | 自动等比缩放 |
| `img_top(sl, name, l, t, w)` | 固定宽度放图，返回实际高度 | 无高度约束 |
| `band(sl, l, t, w, h, color)` | 纯色矩形色带 | 强调/分隔 |
| `hero(sl, l, t, w, h, number, label, accent)` | 大字统计（42pt + 标签） | 关键指标 |
| `cn(sl, x, y, num, color)` | 圆形编号标记（直径 0.5"） | 时间线/步骤 |
| `ft(sl, n)` | 标准页脚：短线 + 机构名 + 页码 | 页脚线在 y=5.25" |
| `st(sl, title)` | 章节标签（8pt + 顶部细线） | 页面顶部 |
| `sT(sl, title, sub)` | 页面主标题（27pt）+ 副标题 | 紧接 `st()` 后 |
| `section_divider(prs, num, title, subtitle)` | 深色章节过渡页 | 章节切换 |
| `ns(prs, bgc)` | 新建空白幻灯片 | layout index 6 |
| `setbg(sl, c)` | 设置纯色背景 | — |
| `_rect(sl, l, t, w, h, color)` | 纯色矩形（内部） | 无边框 |
| `_line(sl, l, t, w, color, thickness)` | 水平细线（内部） | 默认 0.005" |

---

## 5. 设计指导

### 5.1 去 AI 味检查清单

生成 PPT 时必须逐项自查：

- [ ] **无左侧竖线装饰** — 这是 AI 生成 PPT 最常见的视觉指纹。用卡片顶部细横线（0.03" 厚）代替
- [ ] **无 box shadow / 投影效果** — 所有形状用纯色填充，不加阴影
- [ ] **布局不重复** — 至少混合使用 3 种不同布局模式（见 5.3）
- [ ] **有关键指标大字** — 用 `hero()` 展示最重要的 1-3 个数字（42pt+）
- [ ] **有色带打断节奏** — 用 `band()` 在卡片页面之间插入全宽色带作为视觉呼吸
- [ ] **页脚是短线** — 约 1.8 英寸长，不是全宽线
- [ ] **颜色语义化** — 不同信息类型使用不同颜色的卡片顶部强调线（见 Phase 2）
- [ ] **数据具体** — 将具体数值写入卡片正文，不只做定性描述
- [ ] **无 clipart 图标** — 只用几何形状：矩形、线、圆（`cn()`），不用花哨图标

### 5.2 内容密度规则

- 每页最多 8 行文字（不含页脚和章节标签）
- 正文最小字号：卡片内 9.5pt，页脚 7pt
- 卡片 body 可用高度公式：`h_body = h_card - 0.42`（英寸）
- 每行占用高度：`h_line = fs × ls / 72`（英寸）
- 最大可容纳行数：`N_max = floor(h_body / h_line)`

> 详细容量对照表见下文「布局尺寸速查」小节。

### 5.3 页面布局模式

以下为常用布局类型。具体配色和背景由 Phase 2 决定，此处只描述结构。

| 模式 | 结构描述 | 适用场景 |
|------|----------|----------|
| **封面** | 全屏背景色 + 主标题（30-36pt 白）+ 副标题 + 信息区 | 首页 |
| **大纲** | 浅底 + 大号编号（23pt）+ 标题（17pt）+ 一行简短描述 | 目录 |
| **章节过渡** | 深色全屏 + 大号章节号（72pt）+ 章节标题（30pt 白） | 大章节间 |
| **双栏对比** | 左右各一 `cd()`，不同强调线颜色区分 | 基线 vs 改进、已有 vs 本文 |
| **上图下析** | 上半图（55-60% 高度）+ 下半 `cd()` 分析卡 | 数据/图表展示 |
| **左图右文** | 左侧 `plot_card()`（55-60% 宽）+ 右侧 `cd()` | 架构图、流程图 |
| **三图并排** | 三张小图水平排列 + 底部 `band()` 统一结论 | 分布对比 |
| **时间线** | 左侧 `cn()` 圆形序号 + 右侧标题描述，垂直排列 | 贡献、步骤、流程 |
| **Hero 面板** | 1-3 个 `hero()` 大字统计 + 简短分析 | 关键结果汇总 |
| **总结/致谢** | 深色全屏，与封面配色呼应 | 收尾 |

---

## 6. 常见错误速查

| 问题 | 根因 | 预防 |
|------|------|------|
| 卡片 body 文字溢出 | **跳过 Phase 4.2 Step B/C**，凭感觉写 `h_card` | 每个 `cd()` 写之前验算实际渲染行数，套公式反推高度 |
| 页面底部大片空白 | **没有做垂直空间预算（Step A）**，元素高度随便写 | 写代码前列出所有元素的 y/h 并求和，剩余空间均匀分配 |
| 图片变形 | 直接 `add_picture()` 未等比缩放 | 必须用 `img_fit()` |
| 页脚与内容重叠 | 卡片底部超过 y=5.25 | 确保 `y + h ≤ 5.25` |
| 中文显示为宋体 | 未设置 `eaTypeface` | 每条文本加 `rPr.set(qn("a:eaTypeface"), fn)` |
| 配色不一致 | 强调线颜色随意使用 | 回顾 Phase 2 色板，按语义选择颜色 |
| 图片文件缺失 | 路径或文件名错误 | `img_fit()` 已有红色占位符保护，检查 `FIG` 路径 |
| 页面布局单调 | 所有页同一种布局 | 混用至少 3 种页面布局模式（见 5.3） |

---

## 7. 参考资源

- `SKILL_EN.md` — English version of this workflow
