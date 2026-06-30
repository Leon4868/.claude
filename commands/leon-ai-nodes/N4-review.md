# N4: Review

每个 task 完成后必须执行，按**单个 task 粒度**审查。

进入 N4 前必须拿到 N3 输出的「变更文件清单 + 验证结果 + 待审重点」。如果无法区分本 task 改动和用户已有改动，先暂停确认，不得审查整个 working tree 后直接标记完成。

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
- 如果当前环境无法调用 `codex:review`，必须说明原因，并执行一次等价的本地严格自审；高风险任务（认证/支付/数据库/跨模块契约）不得仅靠简略自审放行
- 执行完之后按项目类型运行验证：
  - 前端：在目标前端项目内运行 `yarn lint`；如是 `ai-admin-ui` 或 `ai-decision-system-ui` 且需要自动修复，运行 `yarn fix`；如是 `ai-seat-console`，按需运行 `yarn lint:css`
  - 后端：在 `{BACKEND_ROOT}/ai` 内优先运行相关模块 Maven 测试或至少编译检查；环境依赖阻塞时记录原因
- **审查通过后方可进入 N5**

## 输出给 N5

```text
AI 自审: 通过 / 已修复 / 阻塞
Codex Review: 通过 / 已修复 / 不可用（原因）
验证命令: {命令与结果}
允许标记完成: 是 / 否
```
