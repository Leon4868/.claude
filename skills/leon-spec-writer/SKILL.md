---
name: leon-spec-writer
description: 将需求文档解析为结构化的 requirements.md、design.md、tasks.md，输出到项目 specs/ 目录
---

# leon-spec-writer — 需求规格生成器

将原始需求文档转化为可执行的开发规格。

## 输入

调用者提供原始需求文本 `RAW_DOC`。

## 执行步骤

### 1. 探测项目架构类型

扫描项目根目录，判断架构类型：

- **Monorepo**: 存在 `pnpm-workspace.yaml`、`lerna.json`、`nx.json`、`turbo.json`，或根 `package.json` 含 `workspaces`，或存在 `packages/`、`apps/`、`libs/` 含独立 `package.json`
- **前后端分离**: 存在 `frontend/` + `backend/`（或 `client/` + `server/`、`web/` + `api/`），或多目录含不同语言的包管理文件
- **Web3/智能合约**（可叠加）: 存在 `hardhat.config.ts/js`、`foundry.toml`、`truffle-config.js`、`anchor.toml`，或 `contracts/`、`programs/` 目录含 `.sol`、`.rs`、`.vy` 文件，或依赖含 `hardhat`、`ethers`、`@openzeppelin/contracts`、`viem`、`wagmi`
- **单体应用**: 以上都不命中（默认）

记录为 `ARCH_TYPE`，支持组合（如 `monorepo+web3`、`separated+web3`、`web3`），并收集各模块/包/端的名称和路径。Web3 项目额外收集：合约框架、合约文件路径、链/网络配置、前端 Web3 集成库。

### 2. 读取项目上下文

- 读取 `.claude/CLAUDE.md` 了解项目技术栈
- 读取 `.claude/rules/` 下所有规则文件，了解编码规范
- 根据 `ARCH_TYPE` 扫描对应目录结构，了解现有模块划分
- 检查 `specs/` 目录下是否有已有的 feature specs

### 3. 分析需求

从 `RAW_DOC` 中提取：
- 功能目标（用户要做什么）
- 用户故事（作为 X，我想要 Y，以便 Z）
- 验收标准（怎样算完成）
- 约束条件（性能、安全、兼容性）
- 依赖（需要哪些外部服务或库）

### 4. 推断 feature 名称

根据需求内容生成一个简洁的 kebab-case 名称，如 `user-auth`、`payment-checkout`。

### 5. 创建 specs 目录

```
specs/{feature-name}/
├── requirements.md
├── design.md
└── tasks.md
```

### 6. 生成 requirements.md

```markdown
# {Feature 名称} — 需求规格

## 概述
{一句话描述}

## 用户故事
- 作为 {角色}，我想要 {功能}，以便 {价值}

## 功能需求
1. {F-001} {需求描述}
2. {F-002} {需求描述}
...

## 非功能需求
- 性能: {要求}
- 安全: {要求}
- 兼容性: {要求}

## 验收标准
- [ ] {AC-001} {标准描述}
...

## 依赖
- {外部服务/库}

## 开放问题
- {待确认事项}
```

### 7. 生成 design.md

读取 `.claude/rules/` 确保设计方案符合项目规范。必须包含架构信息：

```markdown
# {Feature 名称} — 技术设计

## 项目架构

- 架构类型: {monorepo | separated | monolith}
- 涉及模块: {本 feature 需要改动的模块/包/端}

## 方案概述
{技术实现思路}

## 架构变更
{涉及哪些模块，如何与现有架构集成}

## 数据模型
{新增/修改的数据结构}

## API 契约
{前后端共用的接口定义 — 请求/响应类型、路由、状态码}

## 组件设计
{新增/修改的组件树，如适用}

## 状态管理
{状态流转，如适用}

## 安全考虑
{基于 security.md 规则的安全设计}

## 技术决策
| 决策 | 选项 | 理由 |
|------|------|------|
```

### 8. 生成 tasks.md

根据 `ARCH_TYPE` 使用对应的 Phase 拆解策略：

- **Monorepo** → 自底向上：shared/types → lib/db/api → app/web → 集成测试
- **前后端分离** → 契约先行：API 契约 → 后端实现 → 前端实现(可 mock) → 联调 → E2E
- **Web3** → 合约先行：合约接口 → 合约实现 → 合约测试+安全审查 → ABI 生成 → 前端 Web3 集成 → 部署测试网 → E2E
- **单体应用** → 按功能模块：基础设施 → 核心功能 → 测试与完善
- 支持叠加（如 `monorepo+web3`）：先按 Web3 顺序处理合约，再按基础架构处理其他模块

```markdown
# {Feature 名称} — 任务清单

## 架构: {ARCH_TYPE}

## 任务列表

### Phase 1: {根据架构类型命名}
- [ ] T-001: {任务描述} `{所属模块/包/端}:{文件路径}` ~{预估时间}

### Phase 2: {根据架构类型命名}
- [ ] T-002: {任务描述} `{所属模块/包/端}:{文件路径}` ~{预估时间}

...

## 依赖关系
- T-002 依赖 T-001
- {Monorepo: 标注跨包依赖}
- {前后端分离: 标注跨端依赖}

## 风险点
- {可能遇到的问题及应对}
```

**任务拆解原则：**

- 每个任务原子性，可独立完成和验证
- 按依赖关系排序（被依赖的先做）
- 标注所属模块/包/端 + 具体文件路径
- 预估完成时间（5min / 15min / 30min / 1h）
- Monorepo: 共享包变更需列出所有消费方
- 前后端分离: 前端可用 mock 并行开发，联调阶段再切真实 API

## 输出

完成后报告：
- Feature 名称
- Specs 路径：`specs/{feature-name}/`
- 总任务数和预估总时间
