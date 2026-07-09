# N3: 执行 Task

## 开始标记

```text
🔨 Task {T-编号}: {任务描述} ~{预估时间}
   Feature {F}/{总F} | 任务 {N}/{总数}
```

## 代码定位与项目约束

执行前必须再次确认本 task 的目标项目/模块（技术栈、文件位置、复用约定见架构画像 `~/.claude/commands/leon-ai-nodes/project-profile.md`）。

约束：

- 不跨项目做无关重构；只修改 task 明确涉及的子项目/模块
- 开发前记录本 task 起始 diff 范围；只把本 task 新增/修改的文件交给 N4 审查，不把用户已有改动误算进任务成果
- 依赖 feature 未完成、接口契约不明确、目标模块无法确认时，必须暂停，不得先写代码占位

## Skill 匹配

根据任务涉及的工种匹配：

- 前端 → skill `leon-frontend-engineer`；后端 → `leon-backend-engineer`；数据库 → `leon-database-engineer`；合约 → `leon-contract-engineer`；没有匹配 → AI 直接执行
- **串行执行**：在当前会话直接调用对应 `leon-*` skill（上下文连贯，最稳）
- **并行执行**：由 N2 派发角色化 subagent（见 N2 的 subagent 表），subagent 内部自行加载同名 skill
- 安全扫描（`leon-security`）保持 skill 串行调用，不做成并行 subagent：它是耗时 CLI 任务，不需要多轮推理；代码审查由 N4 的 AI 自审 + `codex:review` 承担
- 文档同步（`leon-doc-syncer`）在 N5 阶段派发为 subagent（详见 N5）

## 开发

- 参考 design.md 技术设计和 `.claude/rules/` 规范
- 若项目内无 `.claude/`，以本 task 目标项目的 manifest、pom、目录结构和相邻代码为准
- 技术选型自行选最优解，不暂停
- 业务逻辑/产品方向问题 → 暂停与用户沟通
- 如果发现 specs 与现有代码事实冲突，优先相信代码事实；同步记录到 LESSONS.md 候选项，并在必要时暂停确认
- 开发完成后按架构画像「验证命令」运行一次验证（lint / mvn test）；这是本 task 的基准验证，N4 仅在有后续修复时才重跑

## 输出交接给 N4

```text
Task: {T-编号}
目标项目/模块: {路径}
变更文件: {文件清单}
验证结果: {命令 + 结果 / 阻塞原因}
待审重点: {接口契约/数据模型/权限/兼容性等}
```
