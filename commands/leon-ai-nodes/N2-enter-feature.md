# N2: 进入 Feature

1. 读取该 feature 的 requirements.md、design.md、tasks.md
2. 断点恢复：`[x]` 已完成 → 跳过，`[DROPPED]` → 跳过，`[CHANGED]` → 按更新后描述执行
3. 如该 feature 所有任务已完成 → 跳过，进入下一个 feature
4. 如 PLAN.md 标记该 feature 依赖的其他 feature 未完成 → 暂停或跳过该 feature，进入下一个可执行 feature；不得绕过依赖直接开发

## 项目定位

按架构画像 `~/.claude/commands/leon-ai-nodes/project-profile.md` 中的「业务域 → 项目/模块定位启发」，为每个 task 判定具体代码位置。执行计划里每个 task 必须标注目标项目/模块，避免跨项目误改。

若定位结果与 requirements.md / design.md 中的「目标代码位置」冲突，必须先用代码搜索核验；仍无法判断时暂停确认。

## 任务数检查（强制）

读取 tasks.md 后，统计未完成任务数（`[ ]` 的行）：

- **≤8 个** → 正常执行
- **>8 个** → 按 `/leon:prd` Step 5.5 的切分标准（功能闭环 + 依赖最少，每组 4-8 个任务）重新分组拆分：
  - 只有当分组边界清晰、无依赖环、requirements/design 能同步裁剪时，才自动拆分；新 feature 编号取当前 specs 最大整数编号 + 1，同步更新 PLAN.md（新增行、依赖列、状态、执行顺序）并裁剪三份 specs 文件
  - 若无法可靠拆分，暂停并要求用户先回到 `/leon:prd` 调整 specs

## 执行计划

分析 tasks.md 的依赖关系，自行决定串行或并行：

| 串行 | 并行 |
| ---- | ---- |
| 有显式依赖 | 无依赖 |
| 会修改同一文件/模块 | 分属不同代码项目 |
| 涉及共享状态定义（schema、API） | 天然隔离 |
| 需要共享上下文连续推理 | 可用清晰输入/输出交接 |

并行时用 Agent 工具派发**角色化 subagent**（定义在 `~/.claude/agents/leon/`），按工种选择 `subagent_type`：

| 工种 | subagent_type | 何时派发 |
| ---- | ------------- | -------- |
| 前端 | `leon-frontend-engineer` | 前端页面/组件 task |
| 后端 | `leon-backend-engineer` | API/procedure、认证、服务端业务 task |
| 数据库 | `leon-database-engineer` | schema/migration/查询层 task |
| 合约 | `leon-contract-engineer` | 智能合约开发 task |

如果当前环境没有 Agent 工具，或任务边界无法清晰隔离，则退化为主流程串行执行。

派发时在 prompt 里务必传齐：**specs 路径、本次 task 编号与描述、代码项目路径、本 task 已定位的具体项目/模块**（如 `{FRONTEND_ROOT}/ai-admin-ui`、`{BACKEND_ROOT}/ai/ai-dataaccess`；subagent 是冷启动，要靠这些自行加载上下文）。每个 subagent 内部会加载同名 `leon-*` skill 执行，并在最终消息回报「文件清单 + 验证结果 + 待配合事项」。

所有任务都有依赖时退化为全串行（此时不派 subagent，在主流程 inline 调用 skill）。

并行任务回收后必须先合并结果、核对变更文件是否冲突，再进入 N4；如多个 subagent 修改同一文件或同一接口契约，必须暂停人工合并或改为串行。

输出：

```text
📂 Feature {N}/{总数} — {feature名}
📋 执行计划：
  串行 1: T-001(ai-admin) → T-002(ai-admin-ui)
  并行 2: T-003(ai-dataaccess) + T-004(ai-seat-console)
  串行 3: T-005(ai-admin-ui) ← 依赖 T-003, T-004
```
