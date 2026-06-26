# /leon:ai — 自动开发

`$ARGUMENTS` — specs 文件夹路径 + 代码项目路径。

```bash
/leon:ai specs在~/project-specs，代码在~
/leon:ai ~/project/specs 前端~/code/fe 后端~/code/api
```

## 流程图

按此流程执行，到达每个节点时读取 `~/.claude/commands/leon-ai-nodes/` 下对应的节点文件获取详细规则。

```mermaid
flowchart TD
    START([START]) --> N1

    N1["N1: 初始化\n解析输入、扫描 features、加载上下文"]
    N1 --> N2

    N2["N2: 进入 Feature\n读取 specs、分析依赖、输出执行计划"]
    N2 --> N3

    N3["N3: 执行 Task\n检查 skill → 开发"]
    N3 --> N4

    N4["N4: Review\nAI 自审 → Codex Review"]
    N4 --> N5

    N5["N5: 标记完成\ntasks.md 标 x、写 LESSONS.md"]
    N5 --> N6

    N6["N6: QA 评估\n评分决定是否触发 leon-qa-engineer"]
    N6 --> N7

    N7["N7: 上下文管理\n/clear → 重新加载 specs"]
    N7 --> MORE_TASK{还有未完成 task?}

    MORE_TASK -->|YES| N3
    MORE_TASK -->|NO| FEATURE_DONE[Feature 完成 → /clear]

    FEATURE_DONE --> MORE_FEATURE{还有下一个 Feature?}
    MORE_FEATURE -->|YES| N2
    MORE_FEATURE -->|NO| N8

    N8["N8: 完成\n调用 leon-doc-syncer → 输出总结"]
    N8 --> END([END])
```

## 全局规则

**节点执行规则（强制）：**

- 每个节点必须按顺序执行，**严禁跳过任何节点**
- 进入每个节点前，必须先读取 `~/.claude/commands/leon-ai-nodes/` 下对应的节点文件
- 每个节点执行完毕后，必须输出确认行，格式：`✓ [节点名] 完成，进入 [下一节点名]`
- 未完成当前节点前，不得进入下一节点

**节点文件映射（每次必须读取）：**

- N1 → `~/.claude/commands/leon-ai-nodes/N1-init.md`
- N2 → `~/.claude/commands/leon-ai-nodes/N2-enter-feature.md`
- N3 → `~/.claude/commands/leon-ai-nodes/N3-execute-task.md`
- N4 → `~/.claude/commands/leon-ai-nodes/N4-review.md`
- N5 → `~/.claude/commands/leon-ai-nodes/N5-mark-done.md`
- N6 → `~/.claude/commands/leon-ai-nodes/N6-qa-eval.md`
- N7 → `~/.claude/commands/leon-ai-nodes/N7-context.md`
- N8 → `~/.claude/commands/leon-ai-nodes/N8-finish.md`

**暂停：** 业务逻辑歧义、不确定的安全问题、破坏性变更、环境阻塞。
**不暂停：** 纯技术选型 — 选最优解直接执行。

**执行策略：** AI 自主决策串行或并行（无依赖 + 不同项目 → 并行，否则串行）。
