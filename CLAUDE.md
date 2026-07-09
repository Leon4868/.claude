# 全局规则

## Goal 任务：先过 CR 再 commit

固定工作流（适用于所有 /goal 任务）：

1. **写代码阶段绝不提前提交** —— 改动写完先停，**保持留在工作区（未提交）**，让 Stop hook 触发 codex review（`~/.claude/hooks/stop-codex-review-gate.mjs`，审 working-tree 的未提交改动，仅 goal 模式下运行）。
2. **每次某一轮停下时 CR 给 ALLOW，就在那一轮立刻提交这一版**（不攒到最后）：
   - 这一轮有改动、CR **通过 → 提交**。
   - 这一轮 CR **BLOCK → 改 → 再停 → 再 CR**，循环直到**过 → 提交**。
3. 提交完继续后续工作。

铁律：**先过 CR 再 commit，绝不在 CR 之前 commit。**

**Why:** review gate 只审「未提交的 working-tree 改动」。一旦提前 commit，工作区变干净，`hasChanges()` 返回 false，hook 静默放行 → 等于跳过审查。

**误提交补救:** 用 `git reset --soft HEAD~1` 把改动退回工作区再让 hook 审。
