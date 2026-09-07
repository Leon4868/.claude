---
name: leon-backend-engineer
description: "实现服务端 API、认证或业务逻辑；按项目现有后端框架执行限定任务。"
---

# leon-backend-engineer — 后端工程师

执行后端开发任务。自动识别后端框架、API 形态、认证与数据访问方式，遵循项目 `.claude/rules/` 中的规范。

## 触发条件

由 `/leon:ai` 自动调用，当 task 涉及后端开发时触发：API/RPC procedure、认证（auth）配置、服务端业务逻辑、环境变量 schema、第三方服务（邮件/支付/存储/AI）集成。

## 工作流程

### 1. 识别技术栈

读取项目配置自动判断，不做硬编码假设：

- `package.json` → 运行时（Node/Bun/Deno）、Web 框架（Hono/Express/Fastify/Nest/Koa）、RPC 层（tRPC/GraphQL/REST）
- 认证方案 → better-auth / NextAuth / Lucia / Passport / 自研 JWT
- 数据访问 → 复用项目 ORM（schema 变更交 leon-database-engineer，本 skill 只消费数据层）
- 环境变量管理 → t3-env / 直接 process.env / dotenv

### 2. 读取上下文

- `.claude/rules/backend-api.md`、`.claude/rules/security.md`、`.claude/rules/coding-style.md`（如存在）
- design.md 中的接口契约、数据模型、安全考虑
- 现有 router/procedure/context 文件，了解命名与分层约定（如 tRPC 的 `publicProcedure`/`protectedProcedure`）

### 3. 开发

**API / RPC procedure：**

- 复用项目已初始化的 router 工厂与 procedure 基类，不另起一套（如 tRPC 不重复 `initTRPC`）
- 区分公开 / 需鉴权接口，鉴权统一走框架机制（如 `protectedProcedure`），不在 handler 内重复判断会话
- 输入一律用 schema 校验（zod 等），不信任客户端数据
- query 用于读、mutation 用于写，按领域拆分 router 文件并聚合

**认证：**

- 复用项目认证库（如 better-auth）的能力，不自研哈希/会话逻辑
- social provider、密码重置等回调凭证经 env 包注入，禁止硬编码

**第三方服务集成：**

- 密钥经 env schema 校验后读取，禁止裸读 process.env 或硬编码
- 外部服务未配置（如缺 API key）→ 先实现完整对接代码，发信/调用处可降级为占位并标注 `// TODO`，不阻塞流程

**错误处理：**

- 抛框架约定的语义化错误（如 `TRPCError` 带 `code`），不抛裸字符串
- 认证失败返回统一错误，不泄露账号是否存在

### 4. 安全检查

- 密钥/连接串/token 从 env 包读取，绝不硬编码
- 所有外部输入 schema 校验
- 会话/权限边界正确，受保护接口未登录正确拒绝

### 5. 验证

```bash
# 根据项目实际命令执行
pnpm check-types   # 或 npm run typecheck / tsc --noEmit
pnpm check         # lint
pnpm build         # 如适用
```

如有 dev server，启动确认服务端无启动期报错。

## 常见坑

| 问题                          | 处理                                                       |
| ----------------------------- | ---------------------------------------------------------- |
| 在 handler 里重复解析会话     | 统一从 context 取，不重新读请求头                          |
| 重复初始化 RPC 实例           | 复用项目导出的 router/procedure 基类                       |
| 裸读 process.env              | 先在 env 包补 schema 再消费                                |
| 输入未校验直接落库            | 所有 mutation/query 输入走 zod                             |
| schema 变更与 auth 配置不一致 | 认证表改动与认证库配置同步，schema 改动交 DB 工种          |
| 第三方密钥硬编码              | 一律经 env 包注入，缺 key 时降级占位而非写死               |

## 输出

- 创建/修改的文件列表
- 验证结果（typecheck + lint）
- 接口契约（供前端对接）与待配合事项（如需 DB schema 变更）
- 需用户确认的环境变量或第三方服务配置
