# 项目架构画像（唯一维护处）

leon 系列命令（`/leon:ai`、`/leon:prd`、`/leon:init` 及 N1-N5 节点）涉及项目架构信息时，一律以本文件为准，不得在各命令文件中另行复制维护。

路径变量约定：`FRONTEND_ROOT` = 前端代码根目录，`BACKEND_ROOT` = 后端代码根目录，均从命令参数解析或可靠推断，禁止写死某台机器的绝对路径。

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
