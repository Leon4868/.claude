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

## task 执行中

上下文达 80% → 执行 `/compact` 后继续当前 task。

## feature 完成后

执行 `/clear`，进入下一个 feature。

全程自动继续，无需等待用户指令。
