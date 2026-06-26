# N4: Review

每个 task 完成后必须执行，按**单个 task 粒度**审查。

## 1. AI 自审

检查本 task 变更的：

- 代码质量：命名、结构、可读性、是否符合 `.claude/rules/`
- 逻辑正确性：边界条件、错误处理、并发安全
- 安全性：硬编码密钥、`.env` 误入 git、注入漏洞、OWASP Top 10
- 性能：N+1 查询、不必要的重复计算、内存泄漏风险
- 项目边界：变更是否只落在 N2/N3 定位的前端项目或后端 Maven 模块内
- 架构一致性：是否符合现有 Vue 2/Element UI/Vuex/Router/axios 封装，或后端 controller/service/DAO/SQLMap 分层

发现问题立即修复，不确定则暂停。

## 2. Codex Review（强制）

AI 自审通过后，调用 `codex:review`：

- 传入**本 task 涉及的变更文件 diff**（不是整个 working tree）
- 要求 Codex 审查代码质量、逻辑缺陷、安全问题
- 合理建议 → 修复后重新提交复审
- 误报 → 记录理由后忽略
- 执行完之后按项目类型运行验证：
  - 前端：在目标前端项目内运行 `yarn lint`；如是 `ai-admin-ui` 或 `ai-decision-system-ui` 且需要自动修复，运行 `yarn fix`；如是 `ai-seat-console`，按需运行 `yarn lint:css`
  - 后端：在 `{BACKEND_ROOT}/ai` 内优先运行相关模块 Maven 测试或至少编译检查；环境依赖阻塞时记录原因
- **审查通过后方可进入 N5**
