# code-to-ppt

Claude Code 的 PPT 制作 skill，带完整的认知访谈、视觉设计、对抗审查和迭代流程。

## 安装

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -r code-to-ppt ~/.claude/skills/
# 或 git clone https://github.com/ColorsOutofSpace/code-to-ppt.git ~/.claude/skills/code-to-ppt
```

### Codex / OpenCode / OpenClaw

这些工具使用相同的 skill 目录结构：

```bash
# Codex
mkdir -p ~/.codex/skills
cp -r code-to-ppt ~/.codex/skills/

# OpenCode
mkdir -p ~/.config/opencode/skills
cp -r code-to-ppt ~/.config/opencode/skills/

# OpenClaw
mkdir -p ~/.openclaw/skills
cp -r code-to-ppt ~/.openclaw/skills/
```

> 通用规则：找到你当前工具的 skill 目录（通常在 `~/.{tool}/skills/`），把本目录复制进去即可。如果目录结构不同，把 `SKILL.md` + `references/` 放入该工具识别的 skill 路径中。

## 使用

安装后，直接说：

> “帮我做个答辩 PPT”

skill 会带你走完整流程：需求访谈 → 叙事架构 → 视觉方案 → 分组生成 → **即时审查** → 全量对抗审查 → **量化评分迭代** → 交付。

支持任何触发词：PPT、幻灯片、presentation、答辩、汇报、路演、deck、roadmap。

## 文件说明

- `SKILL.md` — skill 主入口，LLM 据此执行全流程
- `references/01_interrogation.md` — 认知访谈 + 风险识别 + 挑战性问题
- `references/02_visual_design.md` — 视觉设计系统
- `references/03_adversarial_review.md` — 对抗审查（含可协商评分）
- `references/04_reflection_loop.md` — 迭代循环
- `references/05_customization.md` — 用户个性化审查标准协商与记忆管理

## 记忆

如选择开启，LLM 会在当前项目目录的 `.code-to-ppt/memory.md` 记录你的偏好。每个项目独立一份，自然隔离。
