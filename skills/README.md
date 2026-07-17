# Skills 技能文档仓库

本仓库收录了 Claude Code 的自定义技能文档，用于记录和复用特定的技术工作流程。

## 📦 仓库信息

- **远程仓库**: http://gitlab.94ai.pro/ai/skills.git
- **本地路径**: `~/.claude/skills` (Claude Code 默认 skills 目录)
- **管理方式**: Git 版本控制
- **技能数量**: 16 个自定义技能

## 什么是 Skill？

Skill 是 Claude Code 的可复用技能包，每个技能文档记录了一个完整的技术工作流程。当遇到相关任务时，Claude Code 可以加载并执行这些技能。

## 现有技能

| 技能 | 描述 | 适用场景 |
|------|------|----------|
| `add-enterprise-config-field` | 在新旧企业配置系统中新增配置字段的完整流程 | 需要在企业配置中添加新字段时使用 |
| `add-legacy-query-param` | 在旧的 iBatis/CustomDAO 架构中新增查询参数 | 使用 iBatis SqlMap 和 CustomDAO 模式的 Legacy 项目 |
| `aliyun-sls-log-query` | 阿里云 SLS 日志服务查询 (自动登录 + 抓 session + POST 取日志) | 排查 data-center / AgentCC / 94AI 生产日志, 按 trace ID / 关键词查日志 |
| `archery-prod-query` | 通过 Archery 查 94AI 生产 MySQL, 只读安全工作流 (自动登录 + session 复用) | 列实例/库/表, 读 ai_task / stat_day_base / t_smart_task 等业务表, 拆分国内/海外口径 |
| `commit-and-deploy` | 交互式提交代码并可选合并到test分支和触发构建 | 需要提交代码、合并到test分支或触发构建时使用 |
| `commit-cn` | 使用中文提交信息提交代码变更 | 需要提交代码并遵循项目提交规范时使用 |
| `find-feign-impl` | 根据 FeignClient 接口定位对应的 Controller 实现 | 从 Feign Client 快速定位到实际 Controller 实现 |
| `find-service-by-url` | 根据请求 URL 映射到对应的微服务工程 | 从请求 URL 快速定位到对应微服务工程 |
| `merge-to-release` | 合并开发分支到 release 上线分支 | 准备上线发版、合并开发分支到 release 分支时使用 |
| `merge-to-test` | 将当前分支合并到 test 分支并推送 | 需要将代码部署到测试环境时使用 |
| `online-issue-triage` | 94AI 线上问题排查方法论 (trace 报错/号码没导入/智能任务没流转) | 串联 SLS 日志、本地代码、Archery 数据库三件套排查线上问题 |
| `release-doc-generator` | 自动生成标准化的发版文档 | 需要生成发版文档、上线文档、部署文档时使用 |
| `requesting-code-review` | 代码审查流程（适配 Java 微服务架构） | 完成任务、实现主要功能或合并前验证代码质量 |
| `tapd` | TAPD 需求管理工具集成 | 创建需求、查询需求、开始开发、创建分支、完成开发等完整开发流程 |
| `trace-api-data-source` | 接口数据源全链路追踪分析方法 | 分析接口业务逻辑和定位数据源（跨服务调用、数据库查询等） |
| `trigger-pipeline` | 使用 GitLab API 触发 CI/CD pipeline | 需要手动触发构建和部署流程时使用 |

## 技能是如何生成的？

这些技能文档是通过 Claude Code 的 **/skills** 命令系统创建和管理的：

1. **创建技能**：使用 `skill-creator` 技能引导创建新的技能文档
2. **技能结构**：每个技能目录包含一个 `SKILL.md` 文件
3. **技能格式**：
   ```markdown
   ---
   name: skill-name
   description: 技能描述
   ---

   # 技能标题

   详细的技能内容...
   ```

## 📥 安装方法

### 首次安装

```bash
# 克隆仓库到 Claude Code 的 skills 目录
git clone http://gitlab.94ai.pro/ai/skills.git ~/.claude/skills

# 或者如果已有 skills 目录，可以克隆到临时目录后移动
git clone http://gitlab.94ai.pro/ai/skills.git ~/temp-skills
cp -r ~/temp-skills/* ~/.claude/skills/
rm -rf ~/temp-skills
```

> **注意**：Claude Code 使用 Git Bash 环境，Windows 和 macOS/Linux 系统都使用相同的命令。

### 更新已有技能

```bash
cd ~/.claude/skills
git pull origin main
```

### 验证安装

安装完成后，可以在 Claude Code 中验证：

```
列出所有可用的技能
```

你应该能看到本仓库中的所有自定义技能。

## 如何使用

### 在 Claude Code 中调用技能

当你需要使用某个技能时，可以直接告诉 Claude：

```
使用 find-feign-impl 技能帮我找到这个 FeignClient 的实现
```

### 查看所有可用技能

```
列出所有可用的技能
```

## 添加新技能

### 方法一：使用 skill-creator

```
创建一个新技能，用于描述 XXX 流程
```

### 方法二：手动创建

1. 创建新目录：`mkdir your-skill-name`
2. 创建 `SKILL.md` 文件，按照以下格式：

```markdown
---
name: your-skill-name
description: 这个技能的简短描述
---

# 技能标题（中文）

## 使用方式

使用这个技能的场景说明...

## 执行步骤

### 步骤一
详细说明...

### 步骤二
详细说明...
```

### AI 维护要求

**重要**：新增技能后，AI 必须同步更新以下文件：

1. **README.md** - 更新"现有技能"表格，添加新技能条目
2. **CLAUDE.md** - 更新两个位置：
   - "仓库结构"部分的目录树
   - "现有技能概览"表格

例如，新增 `your-skill-name` 技能后：
- 在 `README.md` 的技能表格中添加：| `your-skill-name` | 技能描述 |
- 在 `CLAUDE.md` 的目录树中添加：└── your-skill-name/ # 技能说明
- 在 `CLAUDE.md` 的技能表格中添加对应的条目

## 技能文档约定

- 使用中文编写
- 包含具体的使用场景和执行步骤
- 提供代码示例和文件路径
- 遵循 kebab-case 命名规范

## 🔄 Git 管理

本仓库使用 Git 进行版本控制，**只管理自定义 skills**，官方 skills 已通过 `.gitignore` 排除。

### .gitignore 说明

`.gitignore` 已配置排除以下内容：
- **官方 skills**：artifacts-builder、brainstorming、document-skills、example-skills 等
- **测试文件夹**：my-custom-skills、temp-skills 等
- **临时文件**：*.zip 等

**重要**：即使你修改了官方 skills，它们也不会被 Git 追踪，不会出现在 `git status` 中，确保不会被意外提交到远程仓库。

### 同步到远程仓库

```bash
cd ~/.claude/skills

# 添加修改的 skill
git add your-skill-name/

# 提交更改
git commit -m "feat: 添加/更新 your-skill-name 技能"

# 推送到远程
git push origin main
```

### 从远程仓库拉取

```bash
cd ~/.claude/skills
git pull origin main
```

### 提交信息规范

- `feat: 添加新技能` - 新增技能
- `fix: 修复技能问题` - 修复 bug
- `docs: 更新文档` - 更新 README 或 CLAUDE.md
- `refactor: 重构技能` - 重构现有技能

## 相关链接

- [GitLab 仓库](http://gitlab.94ai.pro/ai/skills)
- [Claude Code 文档](https://claude.ai/code)
