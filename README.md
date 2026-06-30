# code-to-ppt

Claude Code 的 PPT 制作 skill，带完整的认知访谈、视觉设计、对抗审查和迭代流程。

## 安装

把本目录复制到 Claude Code 的 skill 目录：

```bash
mkdir -p ~/.claude/skills
cp -r code-to-ppt ~/.claude/skills/
```

## 使用

在 Claude Code 里说：

> “帮我做个答辩 PPT”

skill 会带你走完整流程：需求访谈 → 大纲 → 视觉方案 → 生成 → 审查 → 迭代。

## 文件说明

- `SKILL.md` — skill 主入口，LLM 据此执行全流程
- `references/01_interrogation.md` — 认知访谈方法论
- `references/02_visual_design.md` — 视觉设计系统
- `references/03_adversarial_review.md` — 对抗审查
- `references/04_reflection_loop.md` — 迭代循环

## 记忆

如选择开启，LLM 会在 `~/.config/code-to-ppt/memory/{user_id}.md` 记录你的偏好。
