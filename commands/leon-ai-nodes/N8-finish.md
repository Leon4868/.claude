# N8: 完成

所有 feature 的所有任务完成后：

进入 N8 前必须再次扫描：

- 所有未作废任务均为 `[x]`
- PLAN.md 中 feature 状态与 tasks.md 一致
- 最近一轮 N6 无未解决 QA bug
- N1 记录的用户已有改动未被误覆盖

## 1. 调用 leon-doc-syncer

用 Agent 工具派发 `leon-doc-syncer` subagent（定义在 `~/.claude/agents/leon/`），prompt 传齐 **specs 文件夹路径、本次涉及的代码项目路径、LESSONS.md 路径**。subagent 内部加载同名 skill 执行：

- README 精炼更新（架构 + 业务 + 快速开始）
- .claude/CLAUDE.md 和 rules/ 同步
- specs CHANGELOG 按日期生成
- 文档一致性验证
- 文档同步必须按实际代码位置写清楚前端项目与后端 Maven 模块：
  - 前端根目录 `FRONTEND_ROOT`
  - 后端根目录 `{BACKEND_ROOT}/ai`
  - 涉及的具体项目/模块、验证命令、接口契约和数据库/SQLMap 影响

文档同步只更新与本次 feature/task 相关的内容；不得重写无关 README、CLAUDE.md、rules 或用户自定义章节。发现文档冲突时列入总结，不强行覆盖。

> 如果当前环境没有 Agent 工具，或本次改动范围很小（单 feature、几个文件），可退化为主流程 inline 调用 `leon-doc-syncer` skill，不强制派 subagent。

## 2. 输出总结

```text
🎉 全部完成

📂 Features: {完成数}/{总数}
📋 总任务: {完成数}/{总数}
📝 文档同步: 已完成
🧪 QA: {通过/跳过/阻塞摘要}
✅ 验证: {执行过的关键命令}
⚠️ 未解决事项: {无/列表}

各 Feature 摘要:
- 1.{name}: {N} 个任务 ✅
- 2.{name}: {N} 个任务 ✅
```

如果存在环境阻塞导致的未运行验证、用户需手动处理事项、未自动覆盖的文档冲突，必须在 `⚠️ 未解决事项` 中明确列出。
