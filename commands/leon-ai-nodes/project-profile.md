# 项目架构画像（唯一维护处）

leon 系列命令（`/leon:ai`、`/leon:prd`、`/leon:init` 及 N1-N5 节点）涉及项目架构信息时，一律以本文件为准，不得在各命令文件中另行复制维护。

路径变量约定：`FRONTEND_ROOT` = 前端代码根目录，`BACKEND_ROOT` = 后端代码根目录，均从命令参数解析或可靠推断，禁止写死某台机器的绝对路径。

## 先识别项目，再套画像

本文件收录**多个项目**的画像。N1 必须先判定当前仓库属于哪一个，再只用那一节；**不得把 A 项目的技术栈、目录约定或验证命令套到 B 项目上**。

判定方式（按顺序，命中即停）：

| 信号 | 判定 |
| ---- | ---- |
| 仓库根有 `pnpm-workspace.yaml` 且存在 `apps/api/pyproject.toml` | → **画像 B：enterprise-ai-platform** |
| 存在 `ai-admin-ui/` / `ai-seat-console/` 目录，或 `{BACKEND_ROOT}/ai/pom.xml` | → **画像 A：94AI** |
| 两者都不命中 | **暂停**，要求用户补充架构信息；禁止硬套任一画像 |

新项目接入时在本文件追加一节并补上判定信号，不要改写已有节。

---

# 画像 A：94AI（Vue 2 多前端 + Java 8 Maven 多模块）

## 前端：多项目结构（`FRONTEND_ROOT` 下）

| 项目 | 技术栈 | 包管理 | 常用命令 |
| ---- | ------ | ------ | -------- |
| `ai-admin-ui` | Vue 2.7 + Vue CLI/Webpack + Element UI + Vuex + Vue Router + axios | Yarn | `yarn dev`、`yarn lint`、`yarn fix`、`yarn build:*` |
| `ai-decision-system-ui` | Vue 2.7 + Vue CLI/Webpack + Element UI + Vuex + Vue Router + axios + qiankun/wujie | Yarn | `yarn dev`、`yarn lint`、`yarn fix`、`yarn build:*` |
| `ai-seat-console` | Vue 2.7 + Vite 4 + TypeScript + Element UI + Vuex + Vue Router + qiankun/wujie | Yarn | `yarn dev`、`yarn lint`、`yarn lint:css`、`yarn build:*` |

前端开发约定：

- 优先复用现有 Element UI、`@94ai/common-ui`、Vuex、router、services/axios 封装、`.vue + .es6/.scss` 拆分风格
- `ai-seat-console` 可使用 TypeScript/Vite 生态；另外两个管理端默认保持 JavaScript/Vue CLI 风格
- 主要文件位置：`src/views/`、`src/components/`、`src/router/`、`src/store/`、`src/services/`（seat-console 为 `src/` 下 TS 结构）

## 后端：Maven 多模块 Java 8 工程（根目录 `{BACKEND_ROOT}/ai`）

- 主要模块：`ai-admin`、`ai-open-api`、`ai-server`、`ai-dataaccess`、`ai-domain`、`ai-common`、`ai-cache`、`ai-task`、`ai-sms`、`ai-sms-core`、`ai-decision-system`、`nacos`、`rocketmq`、`kafka` 等
- 技术栈：Spring Boot 2.3.x / Spring Cloud 2.2.x、JFinal、iBatis/SQLMap、Nacos、RocketMQ、Kafka、Redis、MySQL、ClickHouse、MongoDB、Groovy、JUnit 4
- 按 controller/service/domain/dataaccess/sqlmap 分层定位；优先复用现有 DTO/VO/枚举和异常处理方式
- 数据库相关变更必须同步 Java DAO/实体/SQLMap/XML 与必要的脚本或说明

## 业务域 → 项目/模块定位启发

前端 task 在 `FRONTEND_ROOT` 下定位具体项目：

- 管理后台/运营配置/任务管理/AI 配置等 → 优先检查 `ai-admin-ui`
- 决策系统/决策看板/策略决策等 → 优先检查 `ai-decision-system-ui`
- 坐席台/会话工作台/实时接待等 → 优先检查 `ai-seat-console`
- 若 specs 或代码命名无法判断，先用 `rg` 搜索路由、页面、接口名、文案，再决定项目

后端 task 在 `{BACKEND_ROOT}/ai` 下定位具体 Maven 模块：

- 后台管理接口 → 优先 `ai-admin`
- 开放接口 → 优先 `ai-open-api`
- 服务端基础能力 → 优先 `ai-server`
- 数据访问/SQLMap → 优先 `ai-dataaccess`
- 领域模型/公共 DTO → 优先 `ai-domain`、`ai-common`
- 中间件能力 → 按需定位 `ai-cache`、`rocketmq`、`kafka`、`nacos`

定位结果与 specs 中「目标代码位置」冲突时，先用代码搜索核验；仍无法判断时暂停确认。执行时必须先定位具体子项目/模块，再读取该处 manifest、配置、README 和既有代码风格；不要只因为命中了根目录就默认修改所有项目。

## 验证命令

- `ai-admin-ui`、`ai-decision-system-ui`：优先 `yarn lint`；需自动修复时用 `yarn fix`
- `ai-seat-console`：优先 `yarn lint`，必要时加 `yarn lint:css`
- 后端 Maven 模块：优先执行相关模块的 `mvn test` 或 `mvn -pl {module} -am test`；环境依赖导致无法运行时，记录阻塞原因并做静态核查

---

# 画像 B：enterprise-ai-platform（pnpm workspace monorepo）

面向海外游戏业务的 Agent 应用与运行中台。**单仓库**，`FRONTEND_ROOT` 与 `BACKEND_ROOT` 指向同一个仓库根下的不同 app，不是两个独立仓库。

```text
{REPO_ROOT}/
  apps/web/       FRONTEND_ROOT —— React 工作台
  apps/api/       BACKEND_ROOT  —— FastAPI 平台层（治理）
  apps/worker/    dsh 运行时适配（无数据库依赖）
  packages/contracts/  跨端契约唯一真源
  docs/           设计基线      specs/  开发规格
```

## 技术栈

| 层 | 技术 | 包管理 |
| -- | ---- | ------ |
| `apps/web` | React 19 + Vite 6 + TypeScript 5.7（`strict`）+ Tailwind v4 + @xyflow/react + react-router 7；Vitest 3 + Testing Library | pnpm 11 workspace |
| `apps/api` | Python 3.12 + FastAPI + SQLAlchemy 2 (asyncio) + Alembic + pgvector；pytest | uv（独立 venv） |
| `apps/worker` | Python 3.12 + dsh 运行时适配；pytest | uv（独立 venv） |
| `packages/contracts` | TypeScript 类型 + JSON Schema + openapi.yaml | pnpm |

**没有 ESLint / Prettier / ruff / black —— 类型检查就是 lint。** 不要为「补齐工具链」新增 linter。

## 前端约定（`apps/web`）

- 目录按 feature 切：`src/features/<领域>/`，对外只从 `index.ts` 导出；通用件在 `src/components/ui/`，工作台外壳在 `src/components/workspace/`
- **Tailwind v4 没有 `tailwind.config.js`**，主题令牌写在 `src/styles/globals.css` 的 `@theme` 块。只用语义令牌（`text-ink`、`text-muted`、`bg-panel`、`border-line`、`accent-*`），**禁止裸十六进制、禁止新增 CSS 文件**
- 条件类名走 `lib/cn.ts` 的 `cn()`；状态→类名映射表放 `src/styles/variants.ts`，用 `as const`
- 组件一律具名导出 `export function Xxx()`，不用 `export default`、不用 `React.FC`
- 路由集中在 `src/routes.tsx` 的 `createBrowserRouter`，`App.tsx` 是外层布局；**URL 是导航的真源**
- 后端调用一律走 `features/enterprise-api` 的 `EnterpriseApi` 接口，组件里不直接 `fetch`
- **没有数据就展示空态或「待接入」，不编造 mock 数字**（`features/settings/panels/ResourceBudgetPanel.tsx` 是既定基线：指标显示 `--`、按钮 `disabled`）
- 禁止 `any` 与 `@ts-ignore`；仅类型的导入写 `import type`

## 后端约定（`apps/api`）

- 按业务域建目录 `app/<domain>/`，域内固定 `router.py` / `service.py` / `repository.py` / `sql_repository.py` / `schemas.py` / `errors.py` / `tests/`
- 装配只有一处：`app/container.py` 的 `build_container(settings)`
- 端口用 `typing.Protocol`，实现按技术前缀命名 `InMemoryXxx` / `SQLAlchemyXxx`；**业务代码只依赖 Protocol**
- 对外模型继承 `ContractModel`（camelCase 别名），内部继承 `ApiModel`；线上 camelCase，Python 内部 snake_case
- 错误一律抛 `DomainError` 子类，**不在 router 里 `raise HTTPException`**
- **每加一个 SQLAlchemy 仓储必须同时有内存实现**，并在 `container.py` 两个分支成对接线；离线可跑是产品承诺
- 改表唯一入口是 `apps/api/alembic/versions/`，**改表与迁移必须同一个 commit**

## 业务域 → 目标位置定位启发

- 前端页面/画布/工作台 → `apps/web/src/features/<领域>/`；先用 `rg` 搜路由、页面标题、文案确认领域
- 平台治理、模型网关、系统设置 → `apps/web/src/features/settings/`（平台治理已并入系统设置）
- 后端现有域：`agents · knowledge · documents · assets · prompts · skills · tools · governance · orchestration · workflow_runs · workflows · runtime · model_gateway · mcp_registry · identity · audit · persistence · core`
- 新能力先判断能否落进已有域，实在不属于任何一个再开新目录
- **跨前后端的数据形状改动先改 `packages/contracts`**，再改两侧，最后跑契约校验

## 验证命令

唯一入口是 `./scripts/verify.sh`，**不要绕过它直接敲 `pytest` / `vitest`**（会跑到错的解释器或漏掉 `app/*/tests`）：

| 改到哪儿 | 跑什么 |
| -------- | ------ |
| `apps/web` | `./scripts/verify.sh web`（typecheck + vitest + build） |
| `apps/api` | `./scripts/verify.sh api` |
| `apps/worker` | `./scripts/verify.sh worker` |
| `packages/contracts` 或任何契约字段 | `./scripts/verify.sh contracts` |
| 跨端链路 / 数据库 | `./scripts/verify.sh integration` |
| 收尾 | `./scripts/verify.sh all` |

## 该项目的特殊硬约束
- **不直接提交 `main`**；基线取日期最新的 `release_YYYYMMDD`，分支名 `xxl/feature/<需求名>`
- **不静默降级**：HTTP 失败必须暴露成失败；缺配置就明确失败
- **前端不持有模型密钥**；凭证一律 `SecretStr`，只在 `container.py` 装配时取一次明文
- **保持厂商中立**：新依赖若绑定某云专有能力，先停下讨论
