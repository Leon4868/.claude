# ai-admin-ui 工作流执行步进（精确到文件名）

## Context

需求：读懂 `ai-admin-ui` 仓库的 AI 工作流，用「-> 步进」形式说明流程实际是怎么一步步跑起来的、每一步落在哪个文件。

这是一次纯阅读/说明任务，不涉及代码改动。下面是从入口文件到收尾命令的完整调用链，所有路径相对 `fontend-code/ai-admin-ui/`。

---

## 0. 入口加载链（每轮对话必经）

```
.claude/CLAUDE.md                       # 只有一行：@../AGENTS.md
  -> AGENTS.md                          # 项目级硬约束 + 规则优先级 + 上下文加载纪律
       -> 规则优先级：用户明确要求 > 更深层 AGENTS.md > AGENTS.md > Skill 默认流程
       -> 声明「前端需求默认由 $frontend-workflow 路由」
       -> 声明「不得全文读取 .agents/、菜单索引或模块 README」
```

关键点：`AGENTS.md` 只存**事实与硬约束**，不存流程；流程全部在 `.agents/skills/`。

---

## 1. 路由（唯一入口 Skill）

```
.agents/skills/frontend-workflow/SKILL.md
  -> 按需求规模四选一（用户点名 Skill 时直接服从）：
     1) 已有 specs/ 、要求继续未完成任务   -> $frontend-spec-delivery
     2) 有 PRD/TAPD/Issue、跨模块、≥4 个可验证 task -> $frontend-spec-planning
     3) 单点修复 / 样式文案微调 / 局部重构  -> $frontend-implementation
     4) 用户明确要求测试、验收、回归        -> $frontend-qa
  -> 路由后只读被选中的那一个工作流 Skill（最小加载规则）
  -> .agents/skills/frontend-workflow/references/full-workflow.md
       ↑ 仅在「要看完整流程/排查阶段门/维护工作流」时才读（含 mermaid 流程图 + 阶段门总则）
```

---

## 2. 定位层（三个分支共用，每轮只查一个索引）

```
明确菜单名 / 页面名 / 侧边栏入口
  -> rg -n -F "<精确关键词>" .agents/skills/menu-index.md
       -> 命中后：先看真实组件同目录 README.md
            -> 读到 <!-- AI_CONTEXT_END --> 为止（快速上下文）
            -> 再按「专题路由」最多加载 1 个直接相关文档
                 例：src/components/taskDialog/docs/lifecycle.md
       -> 菜单索引查不到时才走 menu-index.md 里的「缺失菜单刷新门禁」
          （只读 localStorage.current_user，受 companyId === 1 门禁约束）

非菜单组件 / 跨目录模块 / 业务专题词
  -> rg -n -F "<精确模块名>" .agents/module-index.md
       -> 取 context 指向的 README.md + 至多一个 docs/*.md
```

纪律：首次查询**不加 `-C`**、不用「管理/页面/模块」这类泛词；结果过多时用菜单 `name`、完整路径、组件名收窄。同一任务不重复读未变化的文件。

---

## 3. 分支 A — 规格规划

```
.agents/skills/frontend-spec-planning/SKILL.md
  -> 读需求来源 + 已有 specs/PLAN.md + 相关 specs
  -> 走第 2 节定位层核对真实页面 / .vue / .es6 / .scss / src/api / router
  -> 选模式：新需求（追加 feature，不改历史）| 需求变更（先找全受影响 feature）
  -> 写入前必读 references/spec-conventions.md
  -> 模板取自 assets/：
       PLAN.template.md / requirements.template.md / design.template.md / tasks.template.md
  -> 四道阶段门（每道门停下等用户，播报「当前阶段 / 已过门 / 下一步」）：
       门 A 切分       -> specs/PLAN.md（feature 行 + 目录）
       门 B requirements -> specs/N.feature-name/requirements.md
       门 C design       -> specs/N.feature-name/design.md
       门 D tasks        -> specs/N.feature-name/tasks.md
  -> 四门全过 = 该 feature「已批准，可进入 delivery」
```

约定：feature 内用 `F-001` / `AC-001` / `T-001`，跨 feature 加 PLAN 序号前缀（`1.T-001`）；PLAN 状态只能是 `未开始` / `进行中` / `已完成` / `已作废`；变更模式保留 `[x]` 与 `[NEW]` `[CHANGED]` `[DROPPED]` 标签。

用户显式说「一次性生成 / 跳过审查 / 直接出全部规格」= 跳过全部门。

---

## 4. 分支 B — 规格交付

```
.agents/skills/frontend-spec-delivery/SKILL.md
  -> ① planning→delivery 交界门：确认规格已批准，否则播报并询问，不擅自开工
  -> ② node .agents/skills/frontend-spec-delivery/scripts/spec-status.mjs
          # 扫 specs/*/tasks.md，输出 已完成/待处理/已放弃 + 下一项 T-NNN
  -> ③ 读 AGENTS.md、specs/PLAN.md、specs/LESSONS.md、当前 feature 三份规格
  -> ④ git status --short --untracked-files=all  # 记录开工前已有改动，不得覆盖/归因
  -> ⑤ 播报进入 delivery + 选下一个依赖已满足的 task

  -> 任务循环（每个 task 一遍）references/task-loop.md：
       1 定位 -> rg 搜 router/菜单/文案/API，成对读 .vue + .es6 + .scss，记 diff 边界
       2 实现 -> 限定在 task 范围，禁顺手重构，优先复用仓库既有实现
       3 验证 -> npm run lint（默认）/ 受影响测试 / npm run addLang（改了 i18n）
       4 审查 -> 只审 task 归属 diff：正确性、边界、清理、i18n、权限、API 契约、安全
       5 记录 -> tasks.md 里只把当前 [ ] 改 [x]；全完成后更新 PLAN.md 状态；
                 非显而易见的决策/限制/踩坑写 specs/LESSONS.md
       6 交接 -> 报 task ID、目标文件、验证命令与结果、人工验证限制、下一个 task

  -> 风险判定 references/risk-and-review.md
       高风险 = 认证授权/权限指令、API 契约、共享组件·hook·store·router·菜单 metadata、
                src/components/agentEdit 图 schema·X6 接线·selection·minimap·测试 drawer、
                feature 最后一个未完成 task
       -> 所有 task 必做本地自审；高风险额外做当前可用的最强独立审查
       -> 高风险 / 收尾 task / 改动 >5 文件且触及共享行为：向用户「推荐」QA，禁自动触发

  -> 完成收尾：
       1 重跑 spec-status.mjs，确认 PLAN 与 tasks 一致
       2 汇总已有验证与剩余风险
       3 QA 决策门      -> 用户同意才进 $frontend-qa；拒绝记 SKIPPED_BY_USER；无答复则停
       4 doc 归档决策门 -> 无论 QA 执行/跳过都要问；同意才进 $frontend-doc-sync
       5 npm run ai:workflow:check   # -> scripts/ai-workflow/validate.mjs
       6 报告改动文件、验证证据、QA 决策、doc 决策、已接受限制、未解外部依赖
  -> 除非用户明确要求，不 commit / push / 合并 / 部署 / 建 PR
```

---

## 5. 分支 C — 直接实现（轻量）

```
.agents/skills/frontend-implementation/SKILL.md
  -> 复用已加载的 AGENTS.md（不重读）
  -> 走第 2 节定位层找真实入口（router 名 / UI 文案 / API 调用 / 同级代码）
  -> 读相关 .vue / .es6 / .scss / 常量 / utils / 子组件
  -> 选范围最小的领域 Skill（见第 6 节）
  -> 实现最小且保持行为的改动；只在已出现真实跨页面复用时才上提共享层
  -> 按 AGENTS.md 跑聚焦检查
  -> 报改动文件、可观察行为、验证结果、动态测试限制
  -> references/localization-checklist.md   ↑ 仅改用户可见文案 / i18n 时，最终确认前读
  -> references/project-conventions.md      ↑ 需要代码风格·目录命名·Common UI 全局约定·
                                              路由·微前端细节时按需读
```

项目专属决策：沿用所在目录 API 风格（Options / Composition 混存，`.vue + .es6/.scss` 配套区域必须保持原结构）；新区域优先 `@94ai/common-ui`，不改范围外稳定 Element UI 页面；新增 i18n key 前查 `src/hooks/index.js` 与附近 `$t(...)`；HTTP 逻辑放 `src/api/`。

---

## 6. 领域 Skill 层（被上面三个分支按最小范围调用）

```
.agents/skills/project-component/SKILL.md      # 页面/组件
   -> references/detailed-guide.md · component-checklist.md · page-examples.md
.agents/skills/common-ui/SKILL.md              # @94ai/common-ui 组件契约
   -> references/nf-table.md · nf-search-form.md · nf-drawer.md · nf-lazy-select.md
      nf-button.md · nf-input.md · nf-confirm.md · nf-message.md · nf-empty.md
      nf-tag.md · nf-text-overflow.md · nf-transfer-select.md · nf-virtual-select.md
      nf-import-template.md
.agents/skills/project-api/SKILL.md            # src/api/ 薄封装
   -> references/api-patterns.md · detailed-guide.md
.agents/skills/project-request-layer/SKILL.md  # 请求层
   -> references/request-checklist.md · detailed-guide.md
.agents/skills/project-store/SKILL.md          # Vuex
   -> references/vuex-patterns.md · detailed-guide.md
.agents/skills/project-i18n-import/SKILL.md    # 多语言
   -> references/import-format.md · detailed-guide.md
```

---

## 7. QA 阶段（永不自动触发）

```
.agents/skills/frontend-qa/SKILL.md
  -> 用户决策门：显式调用 / 明确要求 / 询问后确认 = 已选择；否则先问并等待
     （实现阶段的 lint 与局部测试 ≠ 完整 QA，不得表述为 PASSED）
  -> 读 AGENTS.md 验证基线、package.json / Jest 配置、受影响源码、附近已有测试
  -> references/qa-matrix.md   # 建基于风险的测试矩阵
  -> 先跑范围最小的有效检查，按风险扩大：
       局部展示/样式        -> npm run lint + 聚焦静态检查
       逻辑/共享组件/router/store/请求接线 -> 局部测试，否则评估 npm run test:ci
       i18n 资源            -> npm run addLang
  -> 查 diff 的状态清理、重复提交、loading/异常、请求参数、i18n、权限、router、共享组件兼容
  -> 每条 AC 标 PASS / FAIL / MANUAL/BLOCKED 并附证据
  -> 结论：PASSED | FAILED | NEEDS_MANUAL（跳过时只报 SKIPPED_BY_USER）
```

---

## 8. 文档归档

```
.agents/skills/frontend-doc-sync/SKILL.md
  -> 检查 task/feature 归属 diff 及相关 specs，只更新被实质影响的文档
  -> references/document-ownership.md  # 归属划分
       AGENTS.md      -> 只写反复出现的项目事实与审查规则
       .agents/skills/ -> 可复用流程
       specs/         -> 详细 feature 历史
       根 README      -> 只在安装/架构/命令/用户可见模块描述变化时动
       模块 README    -> 保持 <!-- AI_CONTEXT_END --> 前后一致，禁全文重写
       新模块 README  -> .agents/templates/module-readme.template.md
  -> 已完成 feature 才生成按日期 changelog：specs/CHANGELOG-YYYY-MM-DD.md
  -> 验证所有引用文件、命令、路径、PLAN 状态、task checkbox
```

---

## 9. 提交（仅在明确授权后）

```
.agents/skills/frontend-commit/SKILL.md
  -> 确认用户明确要求 commit，并判断是否另行要求 push
  -> git status --short --untracked-files=all + 已暂存/未暂存 diff + 当前分支 + 近期 commit 主题
  -> 把无关改动与本次范围分开，默认不全量暂存
  -> 跑相关验证（或说明为何跑不了）
  -> 按逻辑分组暂存明确文件 -> git diff --cached 复核
  -> references/commit-types.md  # 中文 Conventional Commit 前缀
  -> 验证 commit 结果与剩余工作区状态
  -> 禁：git add . / -A / --amend / --no-verify / force push / 破坏性历史编辑
  -> 「提交」不等于授权 push / 合并 / 部署 / 触发 pipeline / 建 PR
```

---

## 10. 工作流自身的守卫

```
改了 .agents/ 、模块上下文或 AI 工作流文档
  -> npm run ai:workflow:check
       -> scripts/ai-workflow/validate.mjs
            # 校验每个 SKILL.md 的 YAML frontmatter（name/description）
            # 遍历 .agents/skills/ 全部文件
            # 校验 .agents/module-index.md 与 .agents/templates/module-readme.template.md
```

---

## 仓库当前实际状态（对照参考）

```
specs/PLAN.md                          # 1 个 feature：script-translate-copy（已完成）
specs/1.script-translate-copy/         # requirements.md / design.md / tasks.md
specs/LESSONS.md
specs/CHANGELOG-2026-07-02.md          # 来源 TAPD 1009559 AI话术一键翻译
```

## 三条最容易踩的门

1. **planning 的四道门**（A 切分 / B requirements / C design / D tasks）—— 未获确认不得宣称规格已批准，也不能让 delivery 开工。
2. **QA 门** —— 只有用户明确选择才能跑 `$frontend-qa`；实现阶段的 lint 不算 QA。
3. **doc 归档门** —— 无论 QA 执行还是跳过，都必须单独再问一次。

三道门的共同语义（默认开门、可显式跳过、停下即等待、允许返工、进度播报）定义在
`.agents/skills/frontend-workflow/references/full-workflow.md`。

## 验证方式

本次为纯阅读说明，无改动。如需核对本文档准确性：

```bash
cd fontend-code/ai-admin-ui
npm run ai:workflow:check                                          # 工作流文档自校验
node .agents/skills/frontend-spec-delivery/scripts/spec-status.mjs  # 当前 specs 进度
```
