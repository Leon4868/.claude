# /leon:ai 执行计划 — 个人学习系统（study-sys）

## Context

`/leon:prd` 已在 `/Users/zhizhidemac/Documents/AI/20260730/specs/` 生成了 4 个 feature 的完整 specs（requirements/design/tasks），共 25 个未完成任务，0 个已完成。`/leon:ai` 要求按 `PLAN.md` 的顺序自动执行这些 task：study-login 与 study-record-data 无依赖可并行 → study-record-pages 与 study-dashboard（依赖 study-record-data 的 API）。

本仓库是单仓库 Turborepo monorepo（study-sys），不是 leon-ai-nodes 模板里描述的 Vue 多项目 + Java Maven 多模块架构；该模板的「项目定位」「subagent 工种」章节不适用于本仓库的具体路径命名，但流程本身（N1-N8 循环、断点恢复、Review、QA）照常执行。环境中没有 `leon-frontend-engineer`/`leon-backend-engineer`/`leon-database-engineer` 这类专用 subagent 定义，按 N2 规则退化为主流程内执行（不派发 Agent，直接在主对话中开发+自审）。

补充勘探确认的关键事实（写 specs 时未完全核实，执行前需要据此调整设计细节）：

- `packages/ui/src/components/` 目前只有 `button/card/checkbox/input/label/textarea/skeleton/sonner/...`，**没有 `select` 和 `alert-dialog`**。study-record-form（分类/状态下拉）和删除二次确认都需要先用 `npx shadcn@latest add select alert-dialog -c packages/ui` 引入。
- `packages/db` 没有自己的 `.env`，环境变量靠 `dotenv.config({ path: "../../apps/server/.env" })` 手动加载 `apps/server/.env`（参考 `drizzle.config.ts` 的写法）。新增的 `seed.ts` 必须用同样方式加载 env，否则 `DATABASE_URL` 校验会失败。`packages/db` 需要新增 `tsx` devDependency（目前只有 `apps/server` 有）。
- `apps/server/src/index.ts` 已经挂载好 `/trpc/*` 和 `/api/auth/*`，新增 tRPC router 只需在 `packages/api/src/routers/index.ts` 里挂载即可，不用碰 `apps/server`。
- `apps/web/src/routes/_auth/route.tsx` 的登录保护（`beforeLoad` + `authClient.getSession()` + redirect）已经完整可用，新页面只要放进 `_auth/` 目录即可继承，不需要重新实现。

## 执行策略

按 `PLAN.md` 顺序，在主对话内串行完成 4 个 feature、25 个任务，每个 task 完成后立即执行：自查 → 跑 `pnpm check-types`（该 task 涉及的包）→ 在 `tasks.md` 标记 `[x]` → 必要时记录到新建的 `specs/LESSONS.md`。

执行顺序：

1. **Feature 1 study-login**（6 task）与 **Feature 2 study-record-data**（6 task）——两者互不依赖，文件也基本不重叠（1 改 `apps/web`+`packages/auth`+`packages/db/seed.ts`；2 改 `packages/db/schema`+`packages/api`），按 1→2 顺序串行做（同一对话内手动并行收益有限，串行更不容易出错），先做 2（API 先就绪，1 的 seed 脚本依赖 auth 但不依赖 study-record API，顺序对调也可）。实际执行顺序：**先 2（study-record-data），再 1（study-login）**，因为 3、4 都依赖 2，提前完成 2 能更早解除下游阻塞。
2. **Feature 3 study-record-pages**（7 task，依赖 2）
3. **Feature 4 study-dashboard**（6 task，依赖 2；与 3 无强依赖，但跳转目标存在性更好体验，3 之后做）

## Feature 2: study-record-data（先做）

- T-001 `packages/db/src/schema/study-record.ts`：新建 `study_record` 表（`text` 主键 `crypto.randomUUID()`、`userId` 外键 `text` 关联 `user.id` cascade、`studyDate` date、`title`/`content` not null、`category`/`gains`/`problems`/`nextPlan`/`status` 可空、`durationMinutes` integer not null、时间戳字段、`userId`/`studyDate` 索引），`schema/index.ts` 追加导出。
- T-002/T-003 `packages/api/src/routers/study-record.ts`：`create`/`update`/`delete`/`getById`，全部用 `protectedProcedure`，zod 校验（日期/主题/内容必填、时长 `positive()`），SQL `where` 始终带 `eq(studyRecord.userId, ctx.session.user.id)`，未命中抛 `TRPCError NOT_FOUND`。参考 `routers/todo.ts` 写法风格。
- T-004 `list`：可选 `dateFrom/dateTo/category/keyword`，`keyword` 用 `ilike` 匹配 title/content，默认 `orderBy(desc(studyDate))`。
- T-005 `stats`：今日是否记录、累计天数（`count(distinct studyDate)`）、累计时长、本周时长（本地时区周一起算）、最近 5 条；在 `routers/index.ts` 挂载 `studyRecord` router。
- T-006 联调：起 `pnpm dev:server`，用临时脚本或 trpc panel 验证全部 procedure + 越权用例。

## Feature 1: study-login

- T-001 `apps/web/src/routes/login.tsx`：`showSignIn` 初始值改 `true`，默认展示登录表单。
- T-002 `sign-in-form.tsx`：加「记住登录状态」Checkbox，接入 `authClient.signIn.email` 的 `rememberMe` 参数（需先看 better-auth 1.6.22 类型定义确认参数名是否真的是 `rememberMe`，不是则按实际 API 调整设计）。
- T-003 同文件：登录失败时把 better-auth 返回的错误统一映射为「账号或密码错误」（凭账号枚举防护原则，不展示原始 message）。
- T-004 确认 `_auth/route.tsx` 现有保护逻辑无需改动（已验证可用，仅做行为复核，不写多余代码）。
- T-005 `packages/db/src/seed.ts`：用 `auth.api.signUpEmail` 幂等创建测试账号；新增 `dotenv.config({ path: "../../apps/server/.env" })`；`packages/db/package.json` 加 `tsx` devDependency + `"db:seed": "tsx src/seed.ts"` script。
- T-006 联调：跑 seed → 用测试账号登录成功跳 `/dashboard`，错误密码提示「账号或密码错误」，未登录访问 `/dashboard` 跳 `/login`。

## Feature 3: study-record-pages（依赖 Feature 2 已完成）

- 先用 `npx shadcn@latest add select alert-dialog -c packages/ui` 补齐缺失的 UI 原语（属于 T-001/T-006 的前置步骤，不单独计任务）。
- T-001/T-002 `components/study-record-form.tsx` 共用表单（沿用 `@tanstack/react-form` + zod，参考 `sign-in-form.tsx`）+ `routes/_auth/records/new.tsx`、`routes/_auth/records/$id.edit.tsx`。
- T-003/T-004 `routes/_auth/records/index.tsx` 列表 + `components/study-record-filters.tsx`（筛选条件写入 URL search params）。
- T-005 `routes/_auth/records/$id.tsx` 详情页。
- T-006 用新引入的 alert-dialog 做删除二次确认，接入列表+详情。
- T-007 联调：新增→列表可见→筛选生效→编辑保存→详情更新→删除二次确认。

## Feature 4: study-dashboard（依赖 Feature 2 已完成）

- T-001/T-002 `components/study-stats-cards.tsx` + 改造 `routes/_auth/dashboard.tsx`（移除占位 `privateData` 调试内容）。
- T-003 `components/recent-records-list.tsx`（复用 `stats.recentRecords`，不单独请求 `list`）。
- T-004 首页「新增学习记录」「查看全部记录」入口。
- T-005 加载态优化（Loader 骨架），核对加载时间。
- T-006 联调：统计数字核对、最近记录跳转、按钮跳转。

## 关键文件清单

- `packages/db/src/schema/study-record.ts`（新）、`packages/db/src/schema/index.ts`（改）、`packages/db/src/seed.ts`（新）、`packages/db/package.json`（改）、`packages/db/drizzle.config.ts`（参考不改）
- `packages/api/src/routers/study-record.ts`（新）、`packages/api/src/routers/index.ts`（改）
- `apps/web/src/routes/login.tsx`（改）、`apps/web/src/components/sign-in-form.tsx`（改）
- `apps/web/src/routes/_auth/records/{index,new,$id,$id.edit}.tsx`（新）
- `apps/web/src/components/{study-record-form,study-record-filters,study-stats-cards,recent-records-list}.tsx`（新）
- `apps/web/src/routes/_auth/dashboard.tsx`（改）
- `packages/ui/src/components/{select,alert-dialog}.tsx`（shadcn CLI 新增）

## 验证方式

- 每个 task 完成后跑该包的 `check-types`（如 `pnpm --filter @study-sys/db check-types`、根目录 `pnpm check-types`）。
- Feature 2 完成后用 `pnpm dev:server` + 临时调用（或 `apps/web` 页面联调）验证 tRPC procedure。
- Feature 1/3/4 完成后用 `pnpm dev`（web+server 同时起）在浏览器走完整用户流程：登录 → 新增记录 → 列表筛选 → 详情/编辑/删除 → 首页统计。
- 全部完成后跑根目录 `pnpm build` 确认整体可构建。

## tasks.md 标记规则

每个 task 实际完成（含验证通过）后，立即在对应 `specs/{N}.{feature}/tasks.md` 把 `- [ ] T-00X` 改成 `- [x] T-00X`，不批量收尾再标记。
