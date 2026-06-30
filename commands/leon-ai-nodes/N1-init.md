# N1: 初始化

1. 从 `$ARGUMENTS` 提取 **specs 文件夹路径** 和 **代码项目路径**（可多个）
   - 将前端代码根目录记为 `FRONTEND_ROOT`，后端代码根目录记为 `BACKEND_ROOT`
   - 如未显式传代码项目路径，只能在当前工作目录、specs 相邻目录或 specs 文档中能明确推断时继续；无法可靠推断时暂停要求用户补充路径
2. 验证 `{SPECS_DIR}` 存在：
   - 优先读取 `{SPECS_DIR}/PLAN.md`，按 PLAN 的推荐执行顺序与依赖关系建立 feature 队列
   - 无 PLAN.md 时，扫描 specs 下所有编号目录（`1.xxx/`、`2.xxx/`），按编号升序排列，并标记为旧规格兼容模式
   - 如果既没有 PLAN.md，也没有编号 feature 目录，暂停要求用户先运行 `/leon:prd`
3. 每个待执行 feature 目录须含 requirements.md、design.md、tasks.md；缺任一文件必须暂停修复 specs，不进入 N2
4. 读取 tasks.md 状态，统计 `[ ]`、`[x]`、`[DROPPED]`、`[CHANGED]`、`[NEW]`，建立断点恢复视图
5. 检查 git working tree：
   - 允许存在用户已有改动，但必须记录启动前 diff 摘要
   - 后续 N3/N4/N5 只能处理本轮 task 产生或明确归属本 task 的变更
   - 无法判断归属的改动不得覆盖、不得回滚，暂停询问
6. 加载：代码项目的 `.claude/CLAUDE.md` + `.claude/rules/`
   - 若项目内暂无 `.claude/`，则读取 manifest 和关键配置作为替代上下文：前端读取 `package.json`、构建配置、路由、store、services；后端读取根 `pom.xml`、子模块 `pom.xml`、`src/main/profiles/`、controller/service/dao/sqlmap 结构
7. 加载 `{SPECS_DIR}/LESSONS.md`（架构决策和踩坑记录，开发时必须参考）；文件不存在时视为空记录，不报错
8. 验证各代码项目路径存在，并识别具体项目清单：
   - 前端：`ai-admin-ui`、`ai-decision-system-ui`、`ai-seat-console`
   - 后端：`{BACKEND_ROOT}/ai` Maven 多模块工程
   - 输出本次执行使用的代码路径映射，后续 N2-N8 必须沿用该映射

## 输出

```text
✓ N1 初始化完成
SPECS_DIR: {路径}
执行顺序: {来自 PLAN.md 或编号目录}
路径映射: FRONTEND_ROOT={路径}, BACKEND_ROOT={路径}
断点状态: 未完成 {n}, 已完成 {m}, 作废 {d}, 变更 {c}
启动前已有改动: {无 / 摘要}
```
