# N2: 进入 Feature

1. 读取该 feature 的 requirements.md、design.md、tasks.md
2. 断点恢复：`[x]` 已完成 → 跳过，`[DROPPED]` → 跳过，`[CHANGED]` → 按更新后描述执行
3. 如该 feature 所有任务已完成 → 跳过，进入下一个 feature

## 任务数检查（强制）

读取 tasks.md 后，统计未完成任务数（`[ ]` 的行）：

- **≤8 个** → 正常执行
- **>8 个** → 自动拆分：
  1. 保留前 8 个任务在当前 tasks.md
  2. 将剩余任务写入新 feature 目录 `{N+0.5}.{feature-name}-part2/`（编号取当前最大编号+1）
  3. 新目录复制当前的 requirements.md 和 design.md，tasks.md 只含剩余任务
  4. 输出提示：`⚠️ 任务数超出上限，已自动拆分为 {新feature目录名}`
  5. 继续执行当前 feature

## 执行计划

分析 tasks.md 的依赖关系，自行决定串行或并行：

| 串行 | 并行 |
| ---- | ---- |
| 有显式依赖 | 无依赖 |
| 会修改同一文件/模块 | 分属不同代码项目 |
| 涉及共享状态定义（schema、API） | 天然隔离 |

并行时用 Agent 工具派发**角色化 subagent**（定义在 `~/.claude/agents/`），按工种选择 `subagent_type`：

| 工种 | subagent_type | 何时派发 |
| ---- | ------------- | -------- |
| 前端 | `leon-frontend-engineer` | 前端页面/组件 task |
| 后端 | `leon-backend-engineer` | API/procedure、认证、服务端业务 task |
| 数据库 | `leon-database-engineer` | schema/migration/查询层 task |

派发时在 prompt 里务必传齐：**specs 路径、本次 task 编号与描述、代码项目路径**（subagent 是冷启动，要靠这些自行加载上下文）。每个 subagent 内部会加载同名 `leon-*` skill 执行，并在最终消息回报「文件清单 + 验证结果 + 待配合事项」。

所有任务都有依赖时退化为全串行（此时不派 subagent，在主流程 inline 调用 skill）。

输出：

```text
📂 Feature {N}/{总数} — {feature名}
📋 执行计划：
  串行 1: T-001 → T-002
  并行 2: T-003 + T-004
  串行 3: T-005 ← 依赖 T-003, T-004
```
