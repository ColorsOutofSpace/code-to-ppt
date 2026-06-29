# code-to-ppt

> 认知增强型 PPT 制作系统：从拷打需求到对抗审查，全程进化。

## 简介

code-to-ppt 是一个**认知增强型 PPT 制作 skill**，核心是一个完整的智能工作流：

```
用户说需求 → [拷打引擎] 挖掘真实意图 → [计划管理] 生成可修改计划
    → [记忆系统] 注入偏好和教训 → [执行层] 执行生成
    → [即时反思] 每页即时检查 → [对抗审查] 多 Agent 独立审查
    → [记忆持久化] 保存新发现 → 交付
```

### 核心模块

| 模块 | 职责 | 差异化价值 |
|------|------|-----------|
| **拷打引擎** | 结构化需求挖掘 | 不是问"什么用途"，而是问"如果时间只有一半，你会砍掉什么" |
| **计划管理** | 可交互、可进化的执行计划 | 用户可直接修改任何步骤，计划自动调整依赖关系 |
| **记忆系统** | 跨会话累积偏好和教训 | 用户说"我喜欢冷色调"一次，以后自动记住 |
| **即时反思** | 即时修正，避免重复错误 | 不是事后总结，而是每页生成后立即检查 |
| **对抗审查** | 三 Agent 独立审查 | 创意/逻辑/执行三方交叉验证，发现单 Agent 盲区 |
| **声明式布局** | 代码级精确控制 | 既支持"声明意图"快速生成，也支持"覆盖坐标"精细调整 |

### 与传统 AI PPT 的区别

| 维度 | Gamma/Tome | code-to-ppt |
|------|------------|-------------|
| **输出格式** | 网页/图片（不可编辑） | **原生 .pptx（完全可编辑）** |
| **需求理解** | 接受表面需求 | **拷打挖掘真实意图** |
| **质量保障** | 一次性生成 | **自优化闭环 + 对抗审查** |
| **个性化** | 千篇一律 | **记忆系统累积用户 DNA** |
| **精度控制** | 无法调整 | **声明式 + px 级覆盖** |

## 快速开始

### 安装

```bash
git clone https://github.com/your-username/code-to-ppt.git
cd code-to-ppt
pip install python-pptx pillow
```

### 使用

#### 方式 1：作为 LLM Skill 加载

将本目录添加到 LLM 的 skill 加载路径，然后对话：

```
User: 帮我做一个答辩PPT
AI: [拷打引擎启动] 如果时间只有3分钟，你必须让听众记住什么？
User: 我们的方法在Dice系数上提升了4.7%
AI: [继续拷打] 听众中谁会质疑这个结果？
...
AI: [生成计划] 已为您生成12页计划，请确认或修改...
User: 可以，开始生成
AI: [执行生成 + 即时反思 + 对抗审查]
AI: 已完成！共12页，关键数据已用Hero面板突出。
```

#### 方式 2：作为 Python 库使用

```python
from src.orchestrator import create_orchestrator

# 创建 orchestrator
orch = create_orchestrator(user_id="user_123")

# 启动会话
orch.start_session("基于深度学习的医学影像分析", deck_type="thesis")

# 拷打
summary = orch.run_interrogation("我要做一个硕士答辩PPT")

# 生成计划
plan = orch.generate_plan(summary)

# 计划审查
review = orch.run_adversarial_review(plan, "plan")
if not review.is_passed:
    orch.modify_plan(review.action_items)

# 执行生成
for slide_config in plan["slides"]:
    result = orch.execute_slide(slide_config)
    reflection = orch.reflect_on_slide(result)
    if reflection["needs_correction"]:
        orch.correct_slide(result, reflection)

# 最终审查
final_review = orch.run_adversarial_review(orch.get_full_deck(), "final")

# 结束
orch.end_session()
```

#### 方式 3：声明式快速生成

```python
from src.dual_track_api import SlideDeck

# 创建 deck
deck = SlideDeck(theme="medical")

# 声明式添加页面
deck.add_slide("cover", title="基于深度学习的医学影像分析")

slide = deck.add_slide("two_column_compare", title="研究背景")
slide.add_card(title="现有方法", body="...", accent="warning")
slide.add_card(title="本文方法", body="...", accent="positive")

# 精确覆盖（如果需要微调）
card = slide.add_card(title="详细分析", body="...")
card.override_position(height=1.8)  # 改高度
card.override_typography(font_size=10)  # 改字号

# 构建
deck.build("output.pptx")
```

## 项目结构

```
code-to-ppt/
├── SKILL.md                    # 主 skill 文档（LLM 加载）
├── SKILL_EN.md                 # 英文版 skill 文档
├── SKILL_ORCHESTRATOR.md       # Orchestrator 架构文档
├── reference.md                # Helper 函数参考 + 设计规范
├── README.md                   # 本文件
│
├── src/                        # 核心代码
│   ├── interrogation_engine.py     # 拷打引擎
│   ├── memory_system.py            # 记忆系统
│   ├── adversarial_review.py       # 对抗审查
│   ├── orchestrator.py             # 主控制器
│   ├── layout_manager.py           # 自动布局分配
│   ├── design_contract.py          # 长程一致性
│   └── dual_track_api.py           # 声明式 + 精确控制 API
│
├── prompts/                    # LLM 提示词模板
│   ├── content_parser.md           # 内容解析
│   ├── pattern_recognizer.md       # 模式识别
│   └── slide_mapper.md             # 页面映射
│
└── examples/                   # 示例（待补充）
```

## 核心概念

### 1. 拷打引擎（Interrogation Engine）

不是简单的"问问题"，而是**结构化挖掘真实需求**。

**拷打维度**：
- 核心信息："如果删掉80%，保留哪20%？"
- 受众画像："听众中谁会反对你？"
- 数据突出："哪个数字放大到全屏最能说服人？"
- 视觉约束："你见过哪个PPT觉得'这就是我想要的'？"
- 风险预判："如果听众说'没什么特别的'，你怎么反驳？"

**决策树机制**：根据回答解锁后续问题，直到信息饱和或关键决策完备。

### 2. 记忆系统（Memory System）

**三层记忆结构**：

| 层级 | 内容 | 示例 |
|------|------|------|
| **User Profile** | 稳定偏好 | 色温=冷色，布局偏好=双栏对比 |
| **Error Registry** | 错误及根因 | 第3页文字溢出→根因：未考虑换行 |
| **Insight Cache** | 后期洞察 | 实验结果页用hero面板效果最佳 |

**自动提取**：从对话和执行日志中自动识别偏好和错误，无需手动记录。

**持久化**：`~/.config/code-to-ppt/memory/{user_id}.json`，跨会话累积。

### 3. 对抗审查（Adversarial Review）

**三 Agent 独立审查**：

| Agent | 角色 | 审查维度 |
|-------|------|----------|
| **Creative** | 创意总监 | 视觉吸引力、布局创新、品牌一致性 |
| **Logic** | 逻辑学家 | 论证完整性、信息密度、故事线连贯 |
| **Execution** | 项目经理 | 资源可用性、技术可行性、时间可行性 |

**独立性保证**：每个 Agent 只能看到最终产出，看不到其他 Agent 的输出。

### 4. 声明式布局（Declarative Layout）

**双轨 API**：

```python
# 轨道 1：声明式（快速生成）
slide.add_card(title="问题", body="...", accent="warning")

# 轨道 2：精确覆盖（微调）
card.override_position(height=1.8)
card.override_typography(font_size=10)

# 轨道 3：底层原生（完全自定义）
slide.add_raw(lambda: "直接写 python-pptx 代码")
```

## 配置

### 用户配置

记忆文件默认存储在 `~/.config/code-to-ppt/memory/{user_id}.json`。

可通过环境变量修改：

```bash
export CODE_TO_PPT_MEMORY_DIR="/path/to/memory"
```

### LLM 配置

在 SKILL.md 中配置 LLM 参数：

```yaml
llm_config:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 4000
```

## 贡献

欢迎贡献！请遵循以下流程：

1. **拷打自己的需求**：先问自己"这个功能真的必要吗？"
2. **生成计划**：明确修改哪些文件，预期结果是什么
3. **对抗审查**：让同事独立审查你的设计
4. **即时反思**：每修改一个文件后检查是否引入新问题
5. **记忆更新**：如果发现了新的最佳实践，记录到 Insight Cache

## 许可证

MIT License

## 致谢

- python-pptx：底层 PPT 生成引擎
- 微软 hve-core：YAML 驱动的 PPT skill 参考
- ChatPPT：智能布局匹配参考

---

**让每次 PPT 制作，都比上一次更聪明。**
