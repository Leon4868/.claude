# TAPD Skill

统一的 TAPD 需求管理工具，支持查询需求、开始开发、查看当前任务、完成开发等完整开发流程。

## 功能

- 查询我的需求列表
- 查询本周需求
- 查询需求详情
- 开始开发（创建分支 + 需求文档）
- 查看当前开发任务
- 完成开发（提交代码 + 关联需求）

## 配置

### 快速配置（推荐）

**首次使用时，运行初始化配置向导：**

```bash
cd ~/.claude/skills/tapd/scripts
python init_config.py
```

向导会交互式询问：
1. 项目代码根目录（默认：当前目录的父目录）
2. 项目类型（frontend/backend/fullstack）
3. 需求文档存放目录（默认：~/tapd-requirements）

完成后会生成环境变量设置命令，复制到你的 shell 配置文件即可。

### 手动配置

#### 环境变量

需要设置以下环境变量：

```bash
# TAPD API Token（必需）
export TAPD_TOKEN="your_tapd_token_here"

# 项目代码根目录（必需）
export PROJECT_ROOT_DIR="/path/to/your/project"

# 项目类型（可选，默认为 backend）
export PROJECT_TYPE="backend"  # 或 frontend / fullstack

# 需求文档根目录（可选，默认为 ~/tapd-requirements）
export TAPD_REQUIREMENTS_DIR="/path/to/your/requirements"
```

### 配置文件

配置文件位于 `config/tapd_config.yaml`：

```yaml
tapd:
  base_url: "https://api.tapd.cn"
  workspace_id: "35238004"
  token_env: "TAPD_TOKEN"

project:
  # 项目代码根目录（可通过环境变量 PROJECT_ROOT_DIR 覆盖）
  root_dir: "${PROJECT_ROOT_DIR}"

  # 项目类型：frontend / backend / fullstack
  type: "${PROJECT_TYPE:backend}"

requirement_doc:
  # 支持环境变量，格式：${ENV_VAR:default_value}
  root_dir: "${TAPD_REQUIREMENTS_DIR:~/tapd-requirements}"
  dir_format: "{story_id}_{story_name_short}_{date}"
  max_name_length: 20
  template_file: "templates/requirement_template.md"
```

## 使用方法

### 1. 查询需求

```bash
# 查询我的所有需求
python scripts/workflow/query_stories.py --mode my

# 查询本周需求
python scripts/workflow/query_stories.py --mode week

# 查询需求详情
python scripts/workflow/query_stories.py --mode detail --id 1135238004001234567
```

### 2. 开始开发

```bash
python scripts/workflow/start_dev.py --story-id 1135238004001234567
```

这会：
- 创建开发分支 `feature/tapd-{story_id}`
- 在需求文档目录创建需求文档
- 初始化 Git 仓库（如果需要）

### 3. 提交代码

```bash
python scripts/workflow/commit_with_story.py --story-id 1135238004001234567 -m "实现需求功能"
```

## 目录结构

```
tapd/
├── config/
│   └── tapd_config.yaml          # 配置文件
├── scripts/
│   ├── core/                     # 核心模块
│   │   ├── tapd_api.py          # TAPD API 客户端
│   │   ├── config_manager.py    # 配置管理
│   │   ├── git_helper.py        # Git 操作
│   │   └── requirement_doc_manager.py
│   └── workflow/                 # 工作流脚本
│       ├── query_stories.py     # 查询需求
│       ├── start_dev.py         # 开始开发
│       └── commit_with_story.py # 提交代码
├── templates/
│   └── requirement_template.md   # 需求文档模板
├── skill.md                      # Skill 定义
└── README.md                     # 本文件
```

## 常见问题

### Q: 如何修改需求文档存储位置？

A: 有两种方式：

**方式 1：运行初始化配置向导（推荐）**
```bash
cd ~/.claude/skills/tapd/scripts
python init_config.py
```

**方式 2：手动设置环境变量**
```bash
# Linux/Mac
export TAPD_REQUIREMENTS_DIR="/path/to/your/requirements"

# Windows (PowerShell)
$env:TAPD_REQUIREMENTS_DIR="D:\MyRequirements"

# Windows (CMD)
set TAPD_REQUIREMENTS_DIR=D:\MyRequirements
```

### Q: 如何获取 TAPD Token？

A: 登录 TAPD → 个人设置 → API → 生成 Token

### Q: 需求文档目录命名规则是什么？

A: 默认格式为 `{story_id}_{story_name_short}_{date}`，例如：
```
1135238004001234567_优化登录流程_20260304/
```

可以在 `config/tapd_config.yaml` 中修改 `dir_format` 和 `max_name_length`。
