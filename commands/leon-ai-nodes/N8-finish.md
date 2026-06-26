# N8: 完成

所有 feature 的所有任务完成后：

## 1. 调用 leon-doc-syncer

调用 `leon-doc-syncer` skill 完成文档同步：

- README 精炼更新（架构 + 业务 + 快速开始）
- .claude/CLAUDE.md 和 rules/ 同步
- specs CHANGELOG 按日期生成
- 文档一致性验证
- 文档同步必须按实际代码位置写清楚前端项目与后端 Maven 模块：
  - 前端根目录 `FRONTEND_ROOT`
  - 后端根目录 `{BACKEND_ROOT}/ai`
  - 涉及的具体项目/模块、验证命令、接口契约和数据库/SQLMap 影响

## 2. 输出总结

```text
🎉 全部完成

📂 Features: {完成数}/{总数}
📋 总任务: {完成数}/{总数}
📝 文档同步: 已完成

各 Feature 摘要:
- 1.{name}: {N} 个任务 ✅
- 2.{name}: {N} 个任务 ✅
```
