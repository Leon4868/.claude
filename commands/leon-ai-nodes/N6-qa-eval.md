# N6: QA 评估

AI 动态决策是否触发 `leon-qa-engineer`，不按固定间隔。

## 评分（1-5 分，总分 ≥ 8 触发）

| 维度 | 1 分 | 5 分 |
| ---- | ---- | ---- |
| 变更范围 | 单文件小改动 | 跨多模块/多项目 |
| 风险等级 | 纯 UI 文案 | 数据库/支付/认证 |
| 累积变更 | 上次 QA 后 1 个 task | 上次 QA 后 5+ 个 task |
| 功能边界 | 模块内部实现 | 完整用户可感知功能 |

## 必须触发（无需打分）

- 当前 feature 所有 task 完成
- API 接口变更
- 数据库 migration
- 认证/授权/支付逻辑
- 跨前端项目或跨后端 Maven 模块变更
- 前后端接口契约同时变更
- 连续 5 个 task 未触发过 QA

## 跳过

- 纯文档/注释/配置格式
- 仅新增类型定义（未实现）
- 上一个 task 刚触发过 QA 且当前变更极小

## 触发格式

```text
🧪 触发 QA — 原因: {理由}
   累积变更: {N} 个 task | 风险评估: {总分}
```

## 执行方式

触发后用 Agent 工具派发 `leon-qa-engineer` subagent（定义在 `~/.claude/agents/`），prompt 传齐 **specs 路径、要验证的 feature/task 范围、代码项目路径**。subagent 内部加载同名 skill 执行，回报「测试结果 + 逐条 AC 核验 + bug 清单」。

prompt 中必须包含本次涉及的具体项目/模块清单，例如：

- 前端项目：`{FRONTEND_ROOT}/ai-admin-ui`
- 后端模块：`{BACKEND_ROOT}/ai/ai-admin`、`{BACKEND_ROOT}/ai/ai-dataaccess`
- 需要核验的接口契约、路由、页面入口、SQLMap 或配置文件

> 上下文极少或仅需轻量核验时，也可在主流程 inline 调用 `leon-qa-engineer` skill，不强制派 subagent。

QA 通过 → 继续。发现问题 → 由对应开发工种修复后重新 QA，最多 3 轮。
