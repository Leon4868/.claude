# 项目上下文文档

## 项目概述

**需求 ID**: {story_id}
**需求名称**: {story_name}
**TAPD 链接**: https://www.tapd.cn/35238004/prong/stories/view/{story_id}
**优先级**: {priority}
**目标版本**: {version}

## 项目结构

```
.
├── claude.md              # 本文件 - Claude Code 项目上下文
├── requirement.md         # 需求规格说明文档
├── implementationPlan.md  # 技术实现方案
├── development.md         # 开发进度跟踪
└── release.md            # 发版文档
```

## 核心功能

{description}

## 技术栈

- **目标项目**: {projects}
- **代码仓库路径**: `{code_root_dir}/{projects}`
- **框架**: Spring Boot + MyBatis
- **数据库**: MySQL
- **涉及层次**: Controller → Service → DAO → Mapper XML

## 开发信息

- **开发分支**: `{branch_name}`
- **基准分支**: `{base_branch}`
- **实现状态**: 待实现
- **构建状态**: 待构建
- **待办事项**: 需求分析、代码实现、测试验证、代码评审

## 文档说明

### requirement.md
包含完整的需求分析,包括:
- 需求背景和目标
- 功能详细说明
- 接口变更清单
- 数据库变更(如有)
- 测试用例

### implementationPlan.md
详细的技术实现方案,包括:
- 涉及的文件清单
- 每个文件的具体修改内容
- DTO、Mapper、DAO、XML 各层的变更
- 实现步骤和验证方法

### development.md
开发过程跟踪,记录:
- 分支信息
- 开发进度
- 遇到的问题和解决方案
- 代码提交记录

### release.md
发版文档模板,包含:
- 发版顺序
- SQL 变更脚本
- 配置变更
- 验证方案
- 回滚方案

## 工作流程

1. **需求阶段**: 在 `requirement.md` 中编写需求规格
2. **设计阶段**: 在 `implementationPlan.md` 中制定实现方案
3. **开发阶段**: 在 `development.md` 中跟踪开发进度
4. **发版阶段**: 在 `release.md` 中准备发版文档

## 注意事项

- 这是一个文档项目,不包含实际代码
- 实际代码在对应的微服务工程中
- 所有文档使用中文编写
- 遵循公司的 TAPD 需求管理流程

## 相关技能

在处理此项目时,可以使用以下 Claude Code 技能:

- `tapd`: TAPD 需求管理工具集成
- `commit-cn`: 使用中文提交信息
- `release-doc-generator`: 生成标准化发版文档
- `add-legacy-query-param`: 在旧 iBatis/CustomDAO 架构中新增查询参数
- `trace-api-data-source`: 追踪接口逻辑和数据来源
- `find-service-by-url`: 根据 URL 查找对应的微服务工程

---

**最后更新**: {current_date}
**维护者**: 开发团队
