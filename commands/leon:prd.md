# /leon:prd — 需求文档 → 开发规格生成

支持两种模式：新建需求和需求变更。

## 输入参数

`$ARGUMENTS` 格式：

- **新建模式**：`/leon:prd {项目文件夹路径}`
- **变更模式**：`/leon:prd --change {N}.{feature-name} 变更内容描述`

## 代码上下文

生成 specs 时，如需求涉及现有代码，默认按以下真实项目结构做架构判断与任务切分：

- 前端代码根目录：`FRONTEND_ROOT`
  - `ai-admin-ui`：Vue 2.7、Vue CLI/Webpack、Element UI、Vuex、Vue Router、axios、qiankun/wujie，Yarn
  - `ai-decision-system-ui`：Vue 2.7、Vue CLI/Webpack、Element UI、Vuex、Vue Router、axios、qiankun/wujie，Yarn
  - `ai-seat-console`：Vue 2.7、Vite 4、TypeScript、Element UI、Vuex、Vue Router、axios、qiankun/wujie，Yarn
- 后端 Maven 根目录：`{BACKEND_ROOT}/ai`
  - Maven 多模块 Java 8 工程
  - 主要模块：`ai-admin`、`ai-open-api`、`ai-server`、`ai-dataaccess`、`ai-domain`、`ai-common`、`ai-cache`、`ai-task`、`ai-sms`、`ai-sms-core`、`ai-decision-system`、`nacos`、`rocketmq`、`kafka`
  - 主要技术：Spring Boot 2.3.x、Spring Cloud 2.2.x、JFinal、iBatis/SQLMap、Nacos、RocketMQ、Kafka、Redis、MySQL、ClickHouse、MongoDB、Groovy、JUnit 4

requirements/design/tasks 中凡涉及代码实现，必须写清楚目标前端项目或后端 Maven 模块；无法确定时在开放问题中要求确认，或在设计中说明需要先用代码搜索定位。禁止写死某台机器的绝对路径。

用户提供一个项目文件夹路径，文件夹结构约定：

```text
{项目文件夹}/
├── docs/               ← 需求文档（必须存在，PRD 从这里读取）
└── specs/              ← 所有生成的 specs 都放这里（与 docs 平级）
    ├── PLAN.md         ← 切分索引
    ├── 1.xxx/          ← 已有的 specs（如有）
    ├── 2.xxx/          ← 本次生成的 specs
    └── ...
```

## 模式判断

如果 `$ARGUMENTS` 以 `--change` 开头 → 进入变更模式（跳到「变更模式」章节）
否则 → 进入新建模式

---

## 新建模式

### Step 1: 解析输入，读取需求文档

从 `$ARGUMENTS` 提取项目文件夹路径，记为 `PROJECT_DIR`。所有 specs 产物统一写到 `{PROJECT_DIR}/specs/`（记为 `SPECS_DIR`，不存在则创建）。

读取 `{PROJECT_DIR}/docs/` 下的所有文件作为需求源：

- 支持 `.md`、`.txt`、`.pdf` 等文档格式
- 如果 docs/ 下有多个文件，全部读取并综合分析
- 如果 docs/ 不存在或为空，报错提示用户先在 docs/ 下放入需求文档

### Step 2: 获取项目名称

- 从当前目录的 `package.json` name 字段、`Cargo.toml`、`go.mod` 等提取项目名
- 如无法提取，使用当前目录名
- 转为 kebab-case，记为 `PROJECT_NAME`

### Step 3: 探测项目架构类型

扫描项目根目录、配置文件、目录结构、依赖声明，自行判断架构类型（monorepo / 多仓库 / 单体应用 / Web3 等）。记录 `ARCH_TYPE`。

当前项目 `ARCH_TYPE` 可识别为：前端多项目 + 后端 Maven 多模块的多仓库/多工程架构。生成设计时不得把所有代码描述成单个前后端目录。

### Step 4: 读取项目上下文

- 读取各仓库的 `.claude/CLAUDE.md` 了解技术栈
- 读取 `.claude/rules/` 下所有规则文件
- 扫描目录结构，了解现有模块划分
- 若仓库暂无 `.claude/`，读取前端 `package.json`、构建配置、router/store/services，或后端根/子模块 `pom.xml`、profiles、controller/service/dao/sqlmap 结构

### Step 5: 分析需求

从文档中提取功能目标、用户故事、验收标准、约束条件、依赖。

### Step 5.5: 需求切分（一等步骤，先于任何目录生成）

> **这是整个流程的核心决策步骤，不是事后补丁。** 必须在生成任何 specs 目录之前完成切分。

把 Step 5 得到的功能目标，按「高内聚、可独立交付」原则切成 **N 个 feature**。每个 feature 满足：

- **任务数 4-8 个**（生成 tasks.md 时单 feature 不得超过 8 个任务，见 Step 9）
- 彼此**依赖最少**，能**独立验收**
- 围绕一个清晰的功能闭环（如「登录」「注册」分开，而非塞进一个 `user-auth`）

**预估任务数 ≤ 8 时**：切成 1 个 feature 即可，无需强行拆分。
**预估任务数 > 8 时**：必须拆成多个 feature，禁止把超量任务塞进同一目录。

输出一张**切分表**，作为后续所有步骤的蓝图：

```text
📐 需求切分方案（共 N 个 feature）：

| feature 名称 (kebab-case) | 包含的功能需求            | 预估任务数 | 依赖的 feature |
| ------------------------- | ------------------------- | ---------- | -------------- |
| user-auth-login           | 邮箱登录、手机登录、Tab   | 5          | -              |
| user-auth-register        | 注册、邮箱验证            | 4          | user-auth-login|
```

### Step 5.6: 开放问题确认

完成切分后，如果存在以下情况，**必须暂停并与用户对话确认**，不要自行假设：

- **切分方案本身有争议**（feature 边界不清、某个 feature 任务数可能爆掉、依赖成环）
- 需求描述模糊或有歧义的功能点
- 多种技术实现方案且差异较大
- 缺少关键信息（如目标平台、兼容性要求、第三方服务选型）
- 业务逻辑有矛盾或不完整
- 涉及权限、支付、敏感操作等需要明确确认的功能

格式：

```text
❓ 需要确认以下问题：

1. {问题描述} — {为什么需要确认}
2. {问题描述} — {为什么需要确认}

请逐一回复后继续生成 specs
```

所有问题确认完毕后再进入 Step 6。**切分方案确认后即固化，Step 7-9 严格按切分表逐个 feature 执行。**

### Step 6: 生成 specs 目录与索引

检查 `{SPECS_DIR}/` 下已有的编号目录（如 `1.xxx/`、`2.xxx/`），取最大编号作为起点。**按切分表为每个 feature 依次分配递增编号。**

```text
{PROJECT_DIR}/
├── docs/                            ← 需求文档（输入，与 specs 平级）
└── specs/                          ← = {SPECS_DIR}，所有产物在此
    ├── PLAN.md                      ← 本次 PRD 切分索引（见下）
    ├── 1.比如这是一个已有的标题/     ← 已有 specs
    ├── 2.{feature-1-name}/          ← 本次新建（切分表第 1 个）
    │   ├── requirements.md
    │   ├── design.md
    │   └── tasks.md
    ├── 3.{feature-2-name}/          ← 本次新建（切分表第 2 个）
    │   └── ...
    └── ...
```

**必须生成 `{SPECS_DIR}/PLAN.md`**（已存在则追加本次切分），记录本次 PRD 拆出的所有 feature、执行顺序与依赖，让 `/leon:ai` 知道先做哪个、feature 间如何串联：

```markdown
# 开发计划索引

## 本次 PRD（{YYYY-MM-DD}）切分为 N 个 feature

| 序号 | feature        | 说明       | 依赖     | 状态     |
| ---- | -------------- | ---------- | -------- | -------- |
| 2    | {feature-1}    | {一句话}   | -        | 待开发   |
| 3    | {feature-2}    | {一句话}   | 2        | 待开发   |

**推荐执行顺序**：2 → 3 →（无依赖的可并行）

## ID 编号约定

- 功能需求 / 任务 / 验收标准 ID **在单个 feature 内编号**，跨 feature 用 `{序号}.` 前缀区分。
- 例：`2.T-001` = 序号 2 这个 feature 的 T-001；`3.F-005` = 序号 3 的 F-005。
- **跨 feature 依赖**写全限定 ID，如 `3.T-001 依赖 2.T-004`。
```

> **若切分表只有 1 个 feature**，PLAN.md 仍要生成（只有一行），保持索引一致性。

### Step 7-9 总则：逐 feature 循环

Step 7、8、9 对切分表中的**每个 feature 各执行一遍**，写入各自的目录。下面的模板里 ID 均为 **feature 内编号**（`F-001` / `T-001` / `AC-001`），跨 feature 引用时按 PLAN.md 约定加 `{序号}.` 前缀。

### Step 7: 生成 requirements.md

```markdown
# {Feature 名称} — 需求规格

## 概述

{一句话描述}

## 项目信息

- 项目名: {PROJECT_NAME}
- 架构类型: {ARCH_TYPE}
- 目标代码位置: {前端项目路径/后端模块路径/多个路径}

## 需求版本

| 日期         | 版本 | 说明     |
| ------------ | ---- | -------- |
| {YYYY-MM-DD} | v1   | 初始需求 |

## 用户故事

- 作为 {角色}，我想要 {功能}，以便 {价值}

## 功能需求

1. [F-001] {需求描述}
2. [F-002] {需求描述}

## 非功能需求

- 性能: {要求}
- 安全: {要求}
- 兼容性: {要求}

## 验收标准

- [ ] [AC-001] {标准描述}

## 依赖

- {外部服务/库}

## 开放问题

- {待确认事项}
```

### Step 8: 生成 design.md

**必须先读取项目 `.claude/CLAUDE.md` 和 `.claude/rules/` 下所有规范文件**，设计方案必须遵循项目已有的技术规范和约定。

按功能模块设计，每个模块说明涉及哪些层（前端、后端、数据库、合约等），具体分层根据项目实际架构决定，不做硬编码限制。

```markdown
# {Feature 名称} — 技术设计

## 设计版本

| 日期         | 版本 | 说明     |
| ------------ | ---- | -------- |
| {YYYY-MM-DD} | v1   | 初始设计 |

## 项目架构

- 架构类型: {ARCH_TYPE}
- 涉及层: {根据项目实际情况列出}
- 涉及代码位置: {如 {FRONTEND_ROOT}/ai-admin-ui + {BACKEND_ROOT}/ai/ai-admin}

## 功能模块设计

### 模块 1: {模块名}

{技术方案，遵循 .claude/rules/ 中的规范}

**涉及层及关键设计:**

{根据项目实际分层描述，如数据模型、API 接口、组件设计、合约接口等}

### 模块 2: {模块名}

...

## 接口契约

{API、RPC、合约接口等 — 根据项目类型决定}

## 数据模型

{数据表/模型/链上存储 — 根据项目类型决定}

## 安全考虑

{基于 .claude/rules/security.md 和项目特有的安全规范}

## 技术决策

| 决策 | 选项 | 理由 |
| ---- | ---- | ---- |
```

### Step 9: 生成 tasks.md

**task 的粒度单位是「功能 × 层 的最小可验证切片」，不是「一个完整功能」。** 一个功能通常横跨多层（前端/后端/数据库/合约），按层切成多个可独立验证的 task；AI 执行时读 design.md 自动识别该 task 涉及哪一层。

```markdown
# {Feature 名称} — 任务清单

## 任务版本

| 日期         | 版本 | 说明     |
| ------------ | ---- | -------- |
| {YYYY-MM-DD} | v1   | 初始任务 |

## 项目信息

- 项目名: {PROJECT_NAME}
- 架构类型: {ARCH_TYPE}
- specs 路径: {SPECS_DIR}/{N}.{feature-name}/
- 目标代码位置: {具体前端项目/后端 Maven 模块}

## 任务列表

### 功能 1: {功能名}

- [ ] T-001: 登录接口 POST /login，含入参校验与错误码 ~30min
- [ ] T-002: 登录表单组件与提交联动 ~30min

### 功能 2: {功能名}

- [ ] T-003: {功能切片描述} ~{预估时间}

### 集成与测试

- [ ] T-007: 联调测试 ~{预估时间}
- [ ] T-008: E2E 测试 ~{预估时间}

## 依赖关系

- T-002 依赖 T-001
- 跨 feature 依赖写全限定 ID：本 feature 序号为 3 时，`3.T-001 依赖 2.T-004`

## 风险点

- {可能遇到的问题及应对}
```

> ⛔ **反例**：`T-001: 实现登录功能 ~30min`（横跨前后端+DB，估时必然虚低，且无法独立验证）。
> ✅ **正例**：拆成「登录接口」「登录表单」「session 持久化」三个切片，各自可验证。

**任务拆解原则：**

- 按「功能 × 层」切片，每个切片原子、可独立完成和验证
- 每个 task 标题或说明必须带上目标项目/模块，例如 `ai-admin-ui`、`ai-seat-console`、`ai-admin`、`ai-dataaccess`
- **单个 task 预估时间不得超过 30min**，超过 30min 必须继续拆成多个子任务
- 预估完成时间只能选：5min / 15min / 30min
- **单 feature 任务数 4-8 个**。生成前先数任务总数：若超过 8 个，说明 Step 5.5 切分粒度过粗 —— **回到 Step 5.5 重新切分**（再拆一个 feature 并更新 PLAN.md），**禁止**把超量任务塞进同一目录、也禁止为压到 8 个而虚低估时。

### Step 10: 输出总结

所有 feature 生成完毕后，统一报告：

- 本次 PRD 拆出的 **feature 列表**（序号 + 名称）及 PLAN.md 路径
- 每个 feature 的 specs 路径、涉及技术层、任务数与预估时间
- **总 feature 数、总任务数、预估总时间**
- 推荐执行顺序（来自 PLAN.md）
- 提示用户：**请审查 specs 后，运行 `/leon:ai` 或 `/leon:autoai` 开始开发**

---

## 变更模式

当输入 `/leon:prd --change {N}.{feature-name} 变更内容` 时执行。

### Step C1: 定位入口 feature

先读 `{SPECS_DIR}/PLAN.md` 了解全局 feature 划分与依赖（无 PLAN.md 则按旧单 feature 方式处理）。

在 `{SPECS_DIR}/` 中查找 `--change` 指定的编号目录。如果只传了序号（如 `--change 1`），自动匹配 `1.*` 目录。找不到则报错提示。

### Step C2: 评估变更影响范围（支持跨 feature）

读取入口 feature 的 `requirements.md` / `design.md` / `tasks.md`，结合变更内容判断：**这次变更是否只影响入口 feature？**

- 若变更涉及的功能需求/接口/数据模型**横跨多个 feature**（它们本就是同一 PRD 拆出来的，很常见），依据 PLAN.md 的依赖关系**列出全部受影响的 feature**。
- 输出受影响 feature 清单，**逐个**执行 C3-C7；PLAN.md 也要在 C7 后更新（状态、依赖变化）。

```text
🔎 变更影响范围：入口 2.user-auth-login
  连带影响：3.user-auth-register（共用 session 模块，依赖 2.T-004）
  → 将逐个更新 2、3 两个 feature
```

> 若只影响单个 feature，正常往下走即可，无需展开。

### Step C3: 读取受影响 specs

对**每个受影响 feature**，读取其目录下的：

- `requirements.md` — 当前需求
- `design.md` — 当前设计
- `tasks.md` — 当前任务（注意哪些已完成 `[x]`）

### Step C4: 解析变更内容

变更内容可以是：

- 纯文本描述变更
- 文件路径（新的需求文档）
- URL

### Step C5: 对比分析

将变更内容与每个受影响 feature 的 requirements.md 对比，识别：

- **新增**的功能需求
- **修改**的功能需求
- **删除**的功能需求
- 对验收标准的影响
- **跨 feature 的连带影响**（如修改 2 的接口导致 3 的某任务作废）

> 下面 C6-C8 对**每个受影响 feature 各执行一遍**，写入各自目录。

### Step C6: 更新 requirements.md

- 在「需求版本」表中追加新版本行：

```markdown
## 需求版本

| 日期       | 版本 | 说明             |
| ---------- | ---- | ---------------- |
| 2026-04-11 | v1   | 初始需求         |
| 2026-04-15 | v2   | 新增微信登录方式 |
```

- 在功能需求中标注变更：

```markdown
## 功能需求

1. [F-001] 邮箱 + 密码登录
2. [F-002] 手机号 + 验证码登录
3. [F-003] Tab 切换登录方式
4. [F-004] ~~短信验证码 5 分钟过期~~ `[v2 删除]`
5. [F-005] 微信扫码登录 `[v2 新增]`
6. [F-006] 表单验证 `[v2 修改: 新增微信回调校验]`
```

### Step C7: 更新 design.md

- 追加设计版本
- 新增/修改受影响的功能模块设计
- 不动未受影响的模块
- 标注变更原因

### Step C8: 更新 tasks.md

- 追加任务版本
- 已完成的任务 `[x]` 保持不动
- 受变更影响的未完成任务标记 `[CHANGED]` 并更新描述
- 因变更作废的任务标记 `[DROPPED]`
- 新增的任务标记 `[NEW]`
- 跨 feature 引用按 PLAN.md 约定加 `{序号}.` 前缀（如本 feature 序号为 3 时引用 `2.T-004`）

```markdown
## 任务列表

### 功能 1: 登录表单

- [x] T-001: 创建登录页面和 Tab 切换组件 ~30min
- [x] T-002: 实现邮箱登录表单 ~30min
- [ ] T-003: 实现手机号登录表单 ~30min `[CHANGED v2: 去掉倒计时]`
- [ ] ~~T-004: 短信过期逻辑~~ `[DROPPED v2]`

### 功能 2: 微信登录 `[NEW v2]`

- [ ] T-008: [NEW] 微信 OAuth 回调处理 ~30min
- [ ] T-009: [NEW] 微信登录按钮组件 ~15min
```

### Step C9: 更新 PLAN.md

若本次变更改变了 feature 间依赖、新增了 feature、或让某 feature 作废，**同步更新 `{SPECS_DIR}/PLAN.md`**（依赖列、状态、执行顺序）。无 PLAN.md（旧单 feature 项目）则跳过。

### Step C10: 输出变更摘要

单 feature 变更：

```text
📝 需求变更: 2.user-auth-login v1 → v2

新增: 2 个功能需求, 2 个任务
修改: 1 个功能需求, 1 个任务
删除: 1 个功能需求, 1 个任务
未受影响: 3 个已完成任务保持不动

请产品审查变更后，运行 /leon:autoai 继续开发（会跳过已完成任务）
```

跨多个 feature 变更：

```text
📝 需求变更（影响 2 个 feature）

2.user-auth-login  v1 → v2  ｜新增 2 需求/2 任务，修改 1 需求/1 任务
3.user-auth-register v1 → v2 ｜删除 1 任务 [DROPPED]（依赖的 2.T-004 已变更）
PLAN.md: 已更新 3 对 2 的依赖

未受影响: 共 3 个已完成任务保持不动

请产品审查变更后，运行 /leon:autoai 继续开发（会跳过已完成任务）
```

---

## 示例用法

```bash
# 新建需求 — 提供项目文件夹路径，docs/ 下放需求文档
/leon:prd ~/projects/my-app-specs
/leon:prd /path/to/project-specs

# 需求变更 — 同样基于项目文件夹，指定要变更的 feature
/leon:prd --change 1.user-auth 新增微信扫码登录方式
/leon:prd --change 2 ~/projects/my-app-specs
```
