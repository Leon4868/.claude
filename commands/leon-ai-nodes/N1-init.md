# N1: 初始化

1. 从 `$ARGUMENTS` 提取 **specs 文件夹路径** 和 **代码项目路径**（可多个）
   - 将前端代码根目录记为 `FRONTEND_ROOT`，后端代码根目录记为 `BACKEND_ROOT`
   - 如未显式传代码项目路径，只能在当前工作目录、specs 相邻目录或 specs 文档中能明确推断时继续；无法可靠推断时暂停要求用户补充路径
2. 扫描 specs 下所有编号目录（`1.xxx/`、`2.xxx/`），按编号排列
3. 每个 feature 目录须含 requirements.md、design.md、tasks.md
4. 加载：代码项目的 `.claude/CLAUDE.md` + `.claude/rules/`
   - 若项目内暂无 `.claude/`，则读取 manifest 和关键配置作为替代上下文：前端读取 `package.json`、构建配置、路由、store、services；后端读取根 `pom.xml`、子模块 `pom.xml`、`src/main/profiles/`、controller/service/dao/sqlmap 结构
5. 加载 `{SPECS_DIR}/LESSONS.md`（架构决策和踩坑记录，开发时必须参考）
6. 验证各代码项目路径存在，并识别具体项目清单：
   - 前端：`ai-admin-ui`、`ai-decision-system-ui`、`ai-seat-console`
   - 后端：`{BACKEND_ROOT}/ai` Maven 多模块工程
   - 输出本次执行使用的代码路径映射，后续 N2-N8 必须沿用该映射
