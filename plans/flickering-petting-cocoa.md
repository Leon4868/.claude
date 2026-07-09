# 配置「先过 CR 再 commit」记忆模式

## Context

用户看到别人的 Claude Code 配置里有持久记忆（`~/.claude/projects/<项目>/memory/` 下的 `goal-codex-review-workflow.md` 等文件），希望自己也配置同样的记忆。该记忆固化的工作流是：goal 任务写完代码**先停、不提交**，让 Stop hook（本机对应 `~/.claude/hooks/stop-codex-review-gate.mjs`，本次会话刚加了 goal 模式门控并全局注册到 settings.json）对 working-tree 未提交改动跑 codex review；某轮 CR 给 ALLOW 就在那一轮立刻提交，BLOCK 就改完再停再审，循环直到过。铁律：先过 CR 再 commit——因为 review gate 只审未提交改动，提前 commit 会让 `hasChanges()` 返回 false、hook 静默放行，等于跳过审查。

记忆功能本身是 Claude Code 内置的，无需开关；用户的 memory 目录 `~/.claude/projects/-Users-zhizhidemac--claude/memory/` 已存在但为空。用户已确认：规则要**全局所有项目生效**（写全局 CLAUDE.md），同时在 .claude 项目 memory 里也存一份（和截图一致）。

## 改动内容

### 1. 新建 `~/.claude/CLAUDE.md`（全局，目前不存在）

写入工作流规则，要点：

- goal 任务/有 Stop hook 审查门控时：写完代码先停，**保持改动留在工作区（未提交）**，让 Stop hook 触发 codex review（`~/.claude/hooks/stop-codex-review-gate.mjs`，审 working-tree 未提交改动，仅 goal 模式下运行）。
- 某一轮停下时 CR 给 **ALLOW → 那一轮立刻提交**，不攒到最后；**BLOCK → 改 → 再停 → 再 CR**，循环直到过。
- 铁律：**先过 CR 再 commit，绝不在 CR 之前 commit**。
- Why：review gate 只审未提交的 working-tree 改动，提前 commit 后工作区变干净，`hasChanges()` 返回 false，hook 静默放行 = 跳过审查。
- 若已误提交：`git reset --soft HEAD~1` 把改动退回工作区再让 hook 审。

### 2. 新建 `~/.claude/projects/-Users-zhizhidemac--claude/memory/goal-codex-review-workflow.md`

按标准记忆格式（frontmatter：`name: goal-codex-review-workflow`、`description`、`metadata.type: feedback`），正文为同一工作流 + **Why:** + **How to apply:**，内容与截图对齐但 hook 路径改为本机实际路径。

### 3. 新建 `~/.claude/projects/-Users-zhizhidemac--claude/memory/MEMORY.md`

索引文件，一行指向上面的记忆：
`- [Goal Codex Review 工作流](goal-codex-review-workflow.md) — 先过 CR 再 commit，绝不提前提交`

## 验证

- `cat ~/.claude/CLAUDE.md` 确认内容。
- 新开一个会话（任意项目目录），确认全局 CLAUDE.md 规则被加载（会话上下文中出现该规则）。
- 从 `~/.claude` 启动的会话确认 MEMORY.md 索引被加载。
