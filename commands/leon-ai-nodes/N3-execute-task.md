# N3: 执行 Task

## 开始标记

```text
🔨 Task {T-编号}: {任务描述} ~{预估时间}
   Feature {F}/{总F} | 任务 {N}/{总数}
```

## 代码定位与项目约束

执行前必须再次确认本 task 的目标项目/模块：

- 前端根目录：`FRONTEND_ROOT`
  - `ai-admin-ui`、`ai-decision-system-ui`：Vue 2.7 + Vue CLI/Webpack + Element UI + Vuex + Vue Router，主要文件在 `src/views/`、`src/components/`、`src/router/`、`src/store/`、`src/services/`
  - `ai-seat-console`：Vue 2.7 + Vite + TypeScript，主要文件在 `src/`，优先保持 TS/Vite 现有写法
- 后端根目录：`{BACKEND_ROOT}/ai`
  - Maven 多模块 Java 8，按 controller/service/domain/dataaccess/sqlmap 分层定位
  - 重点模块包括 `ai-admin`、`ai-open-api`、`ai-server`、`ai-dataaccess`、`ai-domain`、`ai-common`、`ai-cache`、`ai-task`、`ai-sms`、`ai-decision-system`

约束：

- 不跨项目做无关重构；只修改 task 明确涉及的子项目/模块
- 前端优先复用现有 Element UI、`@94ai/common-ui`、Vuex、router、services/axios 封装、`.vue + .es6/.scss` 拆分风格
- `ai-seat-console` 可使用 TypeScript/Vite 生态，其他两个管理端默认保持 JavaScript/Vue CLI 风格
- 后端优先复用现有 controller/service/DAO/SQLMap、JFinal/Spring 约定、DTO/VO/枚举和异常处理方式
- 数据库相关变更必须同步 Java DAO/实体/SQLMap/XML 与必要的脚本或说明

## Skill 匹配

根据任务涉及的工种匹配：

| 工种 | 串行（主流程 inline 调用 skill） | 并行（N2 派发 subagent，`subagent_type`） |
| ---- | -------------------------------- | ----------------------------------------- |
| 前端 | skill `leon-frontend-engineer` | `leon-frontend-engineer` |
| 后端 | skill `leon-backend-engineer` | `leon-backend-engineer` |
| 数据库 | skill `leon-database-engineer` | `leon-database-engineer` |
| 合约 | skill `leon-contract-engineer` | （暂无 subagent，串行执行） |
| QA/测试 | skill `leon-qa-engineer` | `leon-qa-engineer`（一般在 N6 派发） |
| 没有匹配 | AI 直接执行 | — |

- **串行执行**：在当前会话直接调用对应 `leon-*` skill（上下文连贯，最稳）。
- **并行执行**：由 N2 用 Agent 工具派发对应 `subagent_type` 的角色化 subagent；subagent 内部会自行加载同名 skill。
- 合约、安全（`leon-security`）、代码审查（`leon-code-reviewer`）、文档同步（`leon-doc-syncer`）按设计保持 skill 串行调用，不做成并行 subagent。

## 开发

- 参考 design.md 技术设计和 `.claude/rules/` 规范
- 若项目内无 `.claude/`，以本 task 目标项目的 manifest、pom、目录结构和相邻代码为准
- 技术选型自行选最优解，不暂停
- 业务逻辑/产品方向问题 → 暂停与用户沟通
- 验证命令按实际项目选择：
  - `ai-admin-ui`、`ai-decision-system-ui`：优先 `yarn lint`；需自动修复时用 `yarn fix`
  - `ai-seat-console`：优先 `yarn lint` 和必要时 `yarn lint:css`
  - 后端 Maven 模块：优先执行相关模块的 `mvn test` 或 `mvn -pl {module} -am test`；若环境依赖导致无法运行，记录阻塞原因并做静态核查
