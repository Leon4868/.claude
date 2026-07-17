# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 仓库定位

这是一个**技能文档仓库** - 收录 Java 微服务开发中的技术工作流程文档。每个目录包含一个 `SKILL.md` 文件，记录特定的开发流程或排查方法。

这些技能专为大 Java 微服务架构设计（Spring Boot、MyBatis/iBatis、Feign Client 架构）。

## 仓库结构

```
skills/
├── .gitignore                         # Git 忽略配置（排除官方 skills）
├── README.md                          # 用户文档
├── CLAUDE.md                          # AI 工作指南（本文件）
├── add-enterprise-config-field/       # 企业配置字段新增流程
├── add-legacy-query-param/            # iBatis/CustomDAO 查询参数新增流程
├── aliyun-sls-log-query/              # 阿里云 SLS 日志查询 (自动登录 + POST 取日志)
├── archery-prod-query/                # Archery 生产 MySQL 只读查询 (自动登录 + session 复用)
├── api-doc-generator/                 # Spring Boot Controller 接口文档生成器
├── commit-and-deploy/                 # 交互式提交代码并可选合并到test分支和触发构建
├── commit-cn/                         # 中文提交信息提交流程
├── find-feign-impl/                   # FeignClient 到 Controller 实现的定位
├── find-service-by-url/               # URL 到微服务工程的映射规则
├── merge-to-release/                  # 合并开发分支到 release 上线分支
├── merge-to-test/                     # 合并到 test 分支并推送
├── online-issue-triage/               # 94AI 线上问题排查方法论 (SLS+代码+Archery)
├── release-doc-generator/             # 自动生成发版文档
├── requesting-code-review/            # 代码审查流程（Java 微服务）
├── tapd/                              # TAPD 需求管理工具集成
├── trace-api-data-source/             # 接口数据源全链路追踪
└── trigger-pipeline/                  # 触发 GitLab CI/CD pipeline
```

每个技能目录包含一个 `SKILL.md` 文件。

**注意**：本仓库只管理自定义 skills，官方 skills（如 artifacts-builder、brainstorming 等）已通过 `.gitignore` 排除，不会被提交到 Git。

## 技能文件格式

每个 `SKILL.md` 文件遵循以下结构：

```markdown
---
name: skill-name
description: 技能用途的简要描述
---

# 技能标题（中文）

详细的中文文档，包含：
- 使用方式
- 分步执行流程
- 文件位置
- 代码示例
- 映射规则
```

frontmatter（`---` 之间的 YAML）包含：
- `name`：机器可读的技能标识符
- `description`：技能用途的简短描述

## 现有技能概览

| 技能 | 用途 |
|-------|---------|
| `add-enterprise-config-field` | 在新旧企业配置系统中新增配置字段的完整流程 |
| `add-legacy-query-param` | 在旧的 iBatis/CustomDAO 架构中新增查询参数的标准化流程 |
| `aliyun-sls-log-query` | 阿里云 SLS 日志服务查询 (自动登录 RAM 用户+TOTP, POST getLogs.json 取日志) |
| `archery-prod-query` | 通过 Archery 查 94AI 生产 MySQL, 只读安全工作流 (Chrome 自动登录 + session 复用) |
| `api-doc-generator` | 为 Spring Boot Controller 生成前端对接接口文档（自动解析 DTO、校验注解、嵌套类型） |
| `commit-and-deploy` | 交互式提交代码并可选合并到test分支和触发构建（支持可选代码审查） |
| `commit-cn` | 使用中文提交信息提交代码变更，遵循项目提交规范 |
| `find-feign-impl` | 根据 FeignClient 接口定位对应的 Controller 实现 |
| `find-service-by-url` | 根据请求 URL 映射到对应的微服务工程和 Controller |
| `merge-to-release` | 合并开发分支到 release 上线分支（校验 test 污染、按发版顺序合并、支持 dry-run） |
| `merge-to-test` | 将当前分支合并到 test 分支并推送到远程 |
| `online-issue-triage` | 94AI 线上问题排查方法论 (trace 报错 / 号码没导入 / 智能任务没流转), 串联 SLS + 代码 + Archery |
| `release-doc-generator` | 自动生成标准化的发版文档（包含 SQL、配置变更、验证方案等） |
| `requesting-code-review` | 完成任务、实现主要功能或合并前使用，验证工作是否符合要求（适配 Java 微服务架构） |
| `tapd` | TAPD 需求管理工具集成（创建需求、查询需求、开始开发、创建分支、完成开发等完整流程） |
| `trace-api-data-source` | 接口业务逻辑和数据源的全链路分析方法 |
| `trigger-pipeline` | 使用 GitLab API 触发 CI/CD pipeline 构建和部署 |

## 新增技能

创建新技能的步骤：

1. 创建以技能命名的新目录（kebab-case 命名）
2. 创建带 frontmatter 的 `SKILL.md` 文件
3. 使用中文编写文档（遵循现有约定）
4. 包含：使用说明、分步流程、文件位置、代码示例
5. **必须同步更新本文件的以下位置**：
   - "仓库结构"部分：在目录树中添加新技能目录
   - "现有技能概览"部分：在表格中添加新技能条目

## AI 维护文档

当新增技能时，必须同时更新以下文件以保持一致性：

| 文件 | 需要更新的位置 |
|------|---------------|
| `README.md` | "现有技能"表格 |
| `CLAUDE.md` | "仓库结构"目录树 + "现有技能概览"表格 |

## Git 管理说明

本仓库使用 Git 进行版本控制，**只管理自定义 skills**。

### .gitignore 配置

`.gitignore` 文件已配置排除所有官方 skills，包括：
- artifacts-builder、brainstorming、brand-guidelines 等官方技能
- document-skills、example-skills 等命名空间技能
- 测试文件夹和临时文件

**重要**：即使修改了官方 skills，它们也不会被 Git 追踪，不会出现在 `git status` 中，确保不会被意外提交。

### 提交规范

- `feat: 添加 xxx 技能` - 新增技能
- `fix: 修复 xxx 问题` - 修复 bug
- `docs: 更新文档` - 更新 README 或 CLAUDE.md
- `refactor: 重构 xxx` - 重构现有技能

### 验证方法

提交前可以使用以下命令验证：
```bash
# 查看被忽略的文件
git status --ignored

# 验证官方 skills 是否被排除
git ls-files | grep -E "^(artifacts-builder|brainstorming|document-skills)"
# 应该返回空结果
```


