# /leon:init — 项目 .claude 初始化

你是一个项目配置初始化助手。你的任务是在当前项目目录中创建 `.claude/` 文件夹及其完整配置结构。

## 执行步骤

## 项目路径提示

初始化时从用户指定路径、当前工作目录或项目 manifest 推断代码根目录，并按角色记录：

- 前端代码根目录：`FRONTEND_ROOT`
  - `ai-admin-ui`：Vue 2.7 + Vue CLI/Webpack + Element UI + Vuex + Vue Router，Yarn
  - `ai-decision-system-ui`：Vue 2.7 + Vue CLI/Webpack + Element UI + Vuex + Vue Router + qiankun/wujie，Yarn
  - `ai-seat-console`：Vue 2.7 + Vite 4 + TypeScript + Element UI + Vuex + Vue Router，Yarn
- 后端 Maven 根目录：`{BACKEND_ROOT}/ai`
  - Maven 多模块 Java 8：`ai-admin`、`ai-open-api`、`ai-server`、`ai-dataaccess`、`ai-domain`、`ai-common`、`ai-cache`、`ai-task`、`ai-sms`、`ai-decision-system`、`nacos`、`rocketmq`、`kafka` 等
  - 主要技术：Spring Boot/Spring Cloud、JFinal、iBatis/SQLMap、Nacos、RocketMQ、Kafka、Redis、MySQL、ClickHouse、MongoDB、JUnit 4

初始化时必须针对具体子项目或后端根工程生成 `.claude/`；不要把前端三个项目和后端多模块混成一个单体规则文件，除非用户明确要求在公共根目录统一初始化。禁止写死某台机器的绝对路径。

### 0. 检测已有 .claude/（前置判断）

在做任何事之前，先检查当前项目根目录是否已存在 `.claude/` 文件夹：

- **不存在** → 这是全新初始化，按第 1～5 步正常生成全部文件。
- **已存在** → 进入「增量补充模式」，**核心原则是保留用户已有内容、只补齐缺失项，绝不覆盖或删除现有内容**。流程如下：

  1. **盘点现有配置**：递归读取 `.claude/` 下所有文件，重点是 `CLAUDE.md` 和 `rules/*.md`，搞清楚：
     - `CLAUDE.md` 已包含哪些章节（技术栈/常用命令/目录结构/规则引入等）；
     - `rules/` 下已有哪些规则文件，各自覆盖了什么内容；
     - 是否存在用户自定义的、不在 leon:init 标准结构内的文件或章节（这些一律保留，不要动）。
  2. **分析项目本身**：执行第 1 步「分析项目」，得出项目当前真实的语言/框架/模块构成（前端、后端 API、数据库、App、合约等）。
  3. **计算差异（标准结构 − 现有内容）**：对照 leon:init 的标准结构（第 2 步的文件结构、第 3 步的 CLAUDE.md 章节、第 5 步的规则内容指引），找出：
     - **缺失的 rules 文件**：项目实际包含某模块（如有数据库）但 `rules/` 中缺对应文件（如 `database.md`）→ 需新建；
     - **CLAUDE.md 缺失的标准章节**：如缺「常用命令」或「目录结构」→ 需补充该章节；
     - **过时/不准确的信息**：如 CLAUDE.md 里的命令、目录结构与项目现状明显不符 → 标记出来，**但不直接改写**，在最终总结里提示用户。
  4. **执行补充（只增不改）**：
     - 新建缺失的 rules 文件，内容基于项目实际推断（遵循第 4、5 步格式与指引）；
     - 向 `CLAUDE.md` 追加缺失的标准章节，以及对新增 rules 文件的 `@rules/xxx.md` 引入行；
     - **已存在的文件和章节一律不改写、不重排、不删除**；如确有冲突或过时内容，只在总结中列出建议，交给用户决定。
  5. **总结报告**：在增量补充模式下，最终输出必须清晰区分三类：
     - ✅ 新建的文件；
     - ➕ 在已有文件中追加的章节/引入行；
     - ⚠️ 检测到的过时/冲突项（仅提示，未自动修改）。

> 增量补充模式下，下文第 2～5 步的「文件结构 / CLAUDE.md 模板 / rules 格式 / 规则内容指引」均作为**生成缺失部分时的参考标准**，而非全量重新生成的指令。

### 1. 分析项目

在生成任何文件之前，先全面分析当前项目：

- 读取 `package.json`、`Cargo.toml`、`go.mod`、`pyproject.toml`、`pom.xml` 等项目描述文件，判断语言和框架
- 扫描目录结构（重点关注 `src/`、`app/`、`lib/`、`tests/`、`migrations/` 等）
- 读取现有的 README、CI 配置、lint 配置、tsconfig 等，提取构建/测试/运行命令
- 识别项目是否包含前端、后端 API、数据库、移动端/桌面 App 等模块

### 2. 生成文件结构

根据分析结果，生成以下结构（只创建与项目相关的文件）：

```
.claude/
├── CLAUDE.md                    # 项目门面，≤150 行
├── rules/
│   ├── coding-style.md          # 命名/缩进/import/注释规范
│   ├── testing.md               # 测试约定、覆盖率要求
│   ├── security.md              # 禁止事项、密钥处理
│   ├── git-workflow.md          # 分支/commit/PR 规范
│   ├── frontend.md              # (如有前端) paths: src/web/**
│   ├── backend-api.md           # (如有后端 API) paths: src/api/**
│   ├── database.md              # (如有数据库) paths: src/db/**, migrations/**
│   ├── app.md                   # (如有移动端/桌面 App) paths: android/**, ios/**, lib/**, native/**
│   └── smart-contract.md        # (如有合约) paths: contracts/**, src/contracts/**
```

### 3. CLAUDE.md 模板

CLAUDE.md 必须包含以下部分，控制在 150 行以内：

```markdown
# {项目名}

{一句话简介}

## 技术栈

- 语言: {lang}
- 框架: {framework}
- 包管理: {pkg manager}

## 常用命令

- 安装依赖: `{install cmd}`
- 开发运行: `{dev cmd}`
- 构建: `{build cmd}`
- 测试: `{test cmd}`
- Lint: `{lint cmd}`

## 目录结构

{树形结构速览，只列关键目录，不超过 20 行}

## 规则

@rules/coding-style.md
@rules/testing.md
@rules/security.md
@rules/git-workflow.md
{以下按需引入}
@rules/frontend.md
@rules/backend-api.md
@rules/database.md
@rules/app.md
@rules/smart-contract.md
```

### 4. rules 文件格式

每个 rules 文件使用以下格式：

```markdown
---
description: { 规则一句话描述 }
globs: { 可选，如 "src/web/**" }
---

# {规则标题}

{具体规则内容，从项目实际配置中推断，简洁明了}
```

### 5. 规则内容指引

- **coding-style.md**: 从 eslint/prettier/editorconfig/rustfmt 等配置推断命名风格、缩进、import 排序、注释规范。如无配置则根据语言社区惯例设定。
- **testing.md**: 从测试框架配置和现有测试推断测试规范、文件命名、覆盖率要求。
- **security.md**: 列出禁止硬编码密钥、环境变量处理、敏感文件 .gitignore 规则等。
- **git-workflow.md**: 从 git 历史推断 commit 风格（conventional commits?），分支命名规范，PR 流程。
- **frontend.md**: 组件规范、状态管理、路由约定等（仅当项目有前端时创建）。
- **backend-api.md**: API 设计规范、错误处理、中间件约定等（仅当项目有后端 API 时创建）。
- **database.md**: migration 规范、ORM 约定、查询规范等（仅当项目有数据库时创建）。
- **app.md**: 移动端/桌面 App 规范，包括导航结构、平台差异处理、原生 API 调用、打包构建、权限申请约定等（仅当项目为 Flutter/React Native/Swift/Kotlin/Expo/Tauri/Electron 等 App 项目时创建，检测 pubspec.yaml、android/、ios/、app.json、expo.config.js、tauri.conf.json、electron.js 等）。
- **smart-contract.md**: 合约安全规范、常见漏洞防范（重入攻击、整数溢出、权限控制）、审计检查清单、测试要求、部署流程等（仅当项目有智能合约时创建，检测 contracts/、hardhat.config、foundry.toml、truffle-config、anchor.toml 等）。

## 重要约束

- 如果 `.claude/` 已存在，进入「增量补充模式」（见下方第 0 步），**禁止整体覆盖或删除用户已有内容**
- 所有规则内容必须基于项目实际情况推断，不要生成空洞的通用规则
- CLAUDE.md 严格控制在 150 行以内
- 只创建与项目实际相关的 rules 文件，不要创建不适用的文件
- 全新初始化时：生成完成后，列出所有创建的文件并给出简要说明
- 增量补充模式时：按第 0 步第 5 项的「总结报告」格式输出（✅ 新建 / ➕ 追加 / ⚠️ 提示），不要谎报为全量初始化
