# N7: 上下文管理

## task 完成后

执行 `/clear`，然后重新读取：

- 当前 feature 的 specs（requirements.md、design.md、tasks.md）
- `{SPECS_DIR}/LESSONS.md`
- 代码项目的 `.claude/CLAUDE.md` + `.claude/rules/`
- 若项目无 `.claude/`，重新加载本次 task 涉及的 manifest/config：
  - 前端：目标项目 `package.json`、构建配置、router、store、services
  - 后端：根 `pom.xml`、目标模块 `pom.xml`、profiles、controller/service/dao/sqlmap 相邻代码
- 保持 N1 输出的代码路径映射：前端 `FRONTEND_ROOT`，后端 `BACKEND_ROOT`

继续下一个 task。

如果当前运行环境不能真正执行 `/clear`，则必须模拟同等效果：

- 丢弃非必要长上下文，只保留 N1 路径映射、当前 feature 状态、LESSONS 摘要、最近 task 交接结果
- 重新读取当前 feature specs 和必要项目规则
- 不依赖记忆中的旧 tasks 状态，必须以磁盘上的 tasks.md 为准

## task 执行中

上下文达 80% → 执行 `/compact` 后继续当前 task。

`/compact` 后必须重新确认：当前 task 编号、目标项目/模块、已修改文件、尚未完成的验证/Review 步骤。

## feature 完成后

执行 `/clear`，进入下一个 feature。

全程自动继续，无需等待用户指令。

但如果 N6 输出 `回流: 暂停`，或发现 tasks.md/PLAN.md 状态不一致，必须停止自动继续并要求修复。
