# GIT_CONVENTIONS

本项目 (`code-to-ppt/`) 是 Obsidian vault 下的多个独立 git 仓库之一。本文规定本项目的 git 仓库布局与提交规范，agent 在本项目工作时必须遵守。

## 仓库布局

`interest/skill/` 是 Obsidian vault 的根目录，**不是 git 仓库**。每个 skill 项目独立成 git 仓库，`.git/` 在各自的项目子目录下。

```
interest/skill/
├── code-to-ppt/           ← 本项目，独立 git 仓库
│   ├── .git/
│   ├── README.md
│   ├── SKILL.md
│   ├── assets/
│   ├── references/
│   └── docs/
├── <other-skill>/         ← 其他 skill 项目（如果有），各自独立 git
│   ├── .git/
│   └── ...
├── .codegraph/            ← vault 级本地工具（不归任何仓库）
├── .omo/                  ← vault 级本地工具（不归任何仓库）
├── docs/                  ← vault 级散文件（不归任何仓库）
└── linuxdo-post.md        ← vault 级散文件（不归任何仓库）
```

## 远程配置

| 项 | 值 |
|---|---|
| 远程名 | `code-to-ppt`（**不是 `origin`**）|
| 远程 URL | `https://github.com/ColorsOutofSpace/code-to-ppt.git` |
| 主分支 | `main`（唯一分支）|

## 提交规范

所有 commit message 描述部分用**中文**。type 前缀沿用 conventional commits 英文（保留历史兼容与过滤能力）。

**Agent commit**（自动，由 agent 触发）：

```
feat: 新增多平台安装支持
refactor: 拆分对抗审查为 4 个独立角色
docs: 重写 README 参照最佳实践
chore: 删除死代码
sync: 更新 README 描述
```

**手动 commit**（人工，由用户触发）：

```
调整L站友链
```

手动 commit 不带 type 前缀，只写一句中文描述。

## 推送规则

- 普通推送：`git push code-to-ppt main`
- 非 fast-forward 时：`git push code-to-ppt main --force-with-lease`
- 禁止 `git push --force`（绕过安全检查，可能盖掉别人/别的环境的提交）
- 强推之前**先 fetch 核对远程 HEAD**，确认要覆盖的就是当前本地 HEAD 的直接父链

## 历史教训（已发生过的强推场景）

本项目远程 main 在本次会话中经历过 4 次 `--force-with-lease` 强推：

1. 撤掉错版 SVG commit
2. 切换 badge 实现（shields.io → shorturl.at 短链）
3. 撤掉多次"调整L站友链"中间版本
4. 重写核心优势对比 section

每次强推前都应确认两件事：(1) 远程 HEAD 没别人推过新东西；(2) 本地 HEAD 是远程 HEAD 的直接后代或能 merge。

## 新建一个 commit 的标准流程

1. 暂存：`git add <files>`
2. 检查：`git status --short && git diff --cached --stat`
3. 提交：`git commit -m "<message>"`
4. 推送：`git push code-to-ppt main`
5. 验证：`git ls-remote code-to-ppt main` 与本地 HEAD 一致
