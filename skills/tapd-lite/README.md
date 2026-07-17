# TAPD Lite - TAPD 轻量级需求管理工具

TAPD 轻量级需求管理工具，专注于核心功能：需求查询、工作流管理、智能分支创建。

## 特性

### 🎯 需求查询
- ✅ 查询我的需求列表（按状态分组）
- ✅ 生成需求详情
- ✅ 查询指定处理人和版本的需求列表

### 🔄 开发工作流
- ✅ 配置初始化（首次使用）
- ✅ 开始开发（更新 TAPD 状态为开发中）
- ✅ 更新需求状态（手动更新 TAPD 状态）
- ✅ 完成开发（标记需求完成）

### 🌿 智能分支管理
- ✅ 智能生成分支名称（自动简化长标题 + 用户确认）
- ✅ 自动查找基础分支（支持正则表达式匹配 `release_20*`）
- ✅ 多项目批量创建分支
- ✅ 交互式确认和自定义

## 快速开始

### 1. 配置环境变量

```bash
# Windows
set TAPD_TOKEN=your_tapd_token_here

# Linux/macOS
export TAPD_TOKEN=your_tapd_token_here
```

### 2. 首次使用 - 配置初始化

```bash
/tapd-lite init
```

或者使用交互式菜单：

```bash
/tapd-lite
```

选择"配置初始化"，按提示输入：
1. **TAPD 用户名**：用于查询你的需求（如：张三）
2. **Git 用户名缩写**：用于分支名前缀（如：zs）
3. **需求文档目录**：存储需求文档的路径（默认：~/tapd-requirements）

### 3. 使用快捷命令

```bash
# 查询我的需求
/tapd-lite my

# 开始开发
/tapd-lite start

# 完成开发
/tapd-lite complete
```

### 4. 创建分支（交互式）

```bash
/tapd-lite
```

选择"生成分支名称并创建分支"，交互流程：
1. 输入需求 ID
2. 自动获取故事信息并简化名称
3. 展示建议的分支名称供确认
4. 用户可选择使用建议名称或自定义修改
5. 选择要创建分支的项目：
   - 仅当前项目
   - 多个项目（从父目录扫描所有 Git 项目）
   - 仅生成分支名称（不创建分支）
6. **自动查找基础分支**（`release_20*` 格式的最新分支）
7. 在选中的项目中创建分支

## 核心功能说明

### 基础分支自动查找

创建分支时会自动：
1. 执行 `git fetch --all` 获取最新远程分支
2. 使用正则表达式匹配分支名称（默认：`^release_20\d{6}$`）
3. 按配置的规则选择最新分支：
   - 优先按分支名称排序（如 `release_20260308` > `release_20260301`）
   - 名称相同时按最后提交时间排序
4. 如果找不到匹配的分支，询问用户选择基础分支

**配置示例**（`config/git_config.yaml`）：
```yaml
base_branch:
  pattern: "^release_20\\d{6}$"  # 匹配 release_20YYMMDD 格式
  fallback: "develop"             # 后备分支
  sort_by: "both"                 # 排序规则：name/commit_time/both
```

## 目录结构

```
tapd-lite/
├── SKILL.md                    # 技能文档（Claude 执行指南）
├── README.md                   # 本文件
├── config/                     # 配置文件
│   ├── tapd_config.yaml       # TAPD API 配置
│   ├── git_config.yaml        # Git 分支配置（含基础分支规则）
│   └── user_config.yaml       # 用户个人配置
└── scripts/                    # Python 脚本
    ├── config_loader.py       # 统一配置加载器
    ├── check_dependencies.py  # 依赖检查脚本
    ├── tapd_client.py         # TAPD API 客户端（含重试机制）
    ├── init_config.py         # 配置初始化脚本
    ├── verify_config.py       # 配置验证脚本
    ├── query_stories.py       # 查询需求脚本
    ├── generate_branch.py     # 生成分支名称脚本
    ├── find_base_branch.py    # 查找基础分支脚本
    ├── extract_story_id.py    # 从分支提取需求ID脚本
    ├── scan_projects.py       # 扫描 Git 项目脚本
    ├── create_branches.py     # 多项目创建分支脚本（含进度显示）
    ├── start_dev.py           # 开始开发工作流脚本
    └── update_status.py       # 更新需求状态脚本
```

## 分支名称生成规则

格式：`{username_abbr}/feature/{short_id}_{story_name_short}`

**Short ID 提取**：从完整 story_id 中提取后7位
- 例如：`1135238004001009034` → `1009034`

### 标题简化示例

| 原标题 | 简化后 | 说明 |
|--------|--------|------|
| 智能任务详情查询 | 智能任务详情查询 | ≤21字符，保持原样 |
| 智能任务策略模板条件支持有效接通次数统计 | 智能任务策略模板条件有效接通次数 | 提取核心关键词 |
| 新版智能任务要覆盖的企业特殊配置 | 新版智能任务企业特殊配置 | 去除"要"、"的"等助词 |

### 完整示例

| 完整 Story ID | Short ID | 故事名称 | 生成的分支名 |
|--------------|----------|---------|-------------|
| 1135238004001009034 | 1009034 | 智能任务详情查询 | `lwk/feature/1009034_智能任务详情查询` |
| 1135238004001009035 | 1009035 | 智能任务策略模板条件支持有效接通次数统计 | `lwk/feature/1009035_智能任务策略模板条件有效接通次数` |

## 依赖

- Python 3.6+
- PyYAML

安装依赖：
```bash
pip install pyyaml
```

## 配置说明

### user_config.yaml（用户配置）

首次使用时通过 `/tapd-lite init` 自动生成：

```yaml
user:
  tapd_username: "张三"          # TAPD 用户名
  git_username_abbr: "zs"        # Git 用户名缩写

paths:
  requirements_dir: "~/tapd-requirements"  # 需求文档目录

initialized: true
```

### tapd_config.yaml（TAPD API 配置）

```yaml
tapd:
  base_url: "https://api.tapd.cn"
  workspace_id: "35238004"
  token_env: "TAPD_TOKEN"

  status_map:
    developing: "开发中"
    resolved: "完成开发"
    # ... 其他状态映射
```

### git_config.yaml（Git 分支配置）

```yaml
git:
  username_abbr: "${GIT_USERNAME_ABBR:lwk}"
  branch_format: "{username_abbr}/feature/{short_id}_{story_name_short}"
  max_story_name_length: 21

  base_branch:
    pattern: "^release_20\\d{6}$"  # 基础分支匹配规则
    fallback: "develop"             # 后备分支
    sort_by: "both"                 # 排序规则
```

## 错误处理

### 网络重试机制

TAPD API 请求失败时自动重试：
- 最多重试 3 次
- 每次重试间隔递增（1秒、2秒、3秒）
- 适用于网络超时、服务器错误（500/502/503/504）

### 错误提示优化

所有脚本都提供清晰的错误提示：
- 配置未初始化：提示运行 `/tapd-lite init`
- Token 未设置：提示设置 `TAPD_TOKEN` 环境变量
- 基础分支未找到：询问用户选择基础分支
- Git 操作失败：显示详细的错误信息

## 与完整版 tapd 的区别

| 功能 | tapd-lite | tapd（完整版） |
|------|-----------|---------------|
| 需求查询 | ✅ | ✅ |
| 工作流管理 | ✅ | ✅ |
| 智能分支创建 | ✅ | ✅ |
| 基础分支自动查找 | ✅ | ❌ |
| 配置初始化 | ✅ | ✅ |
| 需求分析 | ❌ | ✅ |
| 代码编写辅助 | ❌ | ✅ |
| 发版文档生成 | ❌ | ✅ |

**tapd-lite** 专注于核心的需求管理和分支创建功能，适合快速、轻量的使用场景。

## 完整使用示例

### 场景：从零开始使用 tapd-lite 创建开发分支

**步骤 1：安装依赖**

```bash
cd /path/to/tapd-lite
python scripts/check_dependencies.py --install
```

输出：
```
Installing missing dependencies...
  Installing pyyaml... ✓
✓ All dependencies are installed
```

**步骤 2：配置环境变量**

```bash
# Windows
set TAPD_TOKEN=your_token_here

# Linux/macOS
export TAPD_TOKEN=your_token_here
```

**步骤 3：初始化配置**

```bash
/tapd-lite init
```

按提示输入：
- TAPD 用户名：张三
- Git 用户名缩写：zs
- 需求文档目录：~/tapd-requirements（或自定义）

输出：
```
✅ 配置初始化完成：

TAPD 用户名: 张三
Git 用户名缩写: zs
需求文档目录: ~/tapd-requirements

Verifying configuration...
User Config: ✓ User configuration is valid
TAPD Token: ✓ TAPD token is set (TAPD_TOKEN)
```

**步骤 4：查询我的需求**

```bash
/tapd-lite my
```

输出：
```
你的需求（共 15 个）：

规划中（3个）：
  [1009034] 智能任务详情查询 (状态: 规划中, 优先级: 4)
  [1009035] 智能任务策略模板 (状态: 规划中, 优先级: 4)
  [1009036] 数据统计优化 (状态: 规划中, 优先级: 3)

开发中（2个）：
  [1009030] 用户权限管理 (状态: 开发中, 优先级: 4)
  [1009031] 日志系统升级 (状态: 开发中, 优先级: 3)
```

**步骤 5：开始开发**

```bash
/tapd-lite start
```

选择需求 `[1009034] 智能任务详情查询`，输出：
```
✅ 开发准备完成：

需求ID: 1135238004001009034
需求名称: 智能任务详情查询
文档目录: ~/tapd-requirements/1135238004001009034_智能任务详情查询_20260315
TAPD 状态: 已更新为"开发中"

生成的文档：
- requirement.md - 需求原文
- development.md - 开发信息（分支名称、涉及项目）
- release.md - 发版文档模板
```

**步骤 6：创建分支**

```bash
/tapd-lite
```

选择"生成分支名称并创建分支"：
1. 输入需求ID：1135238004001009034
2. 确认分支名称：`zs/feature/1009034_智能任务详情查询`
3. 选择项目范围：多个项目
4. 选择项目：api-service, web-frontend

输出：
```
Processing 1/2: api-service...
  ✓ Branch created successfully from release_20260308
Processing 2/2: web-frontend...
  ✓ Branch created successfully from release_20260308

✅ 分支创建完成：

分支名称: zs/feature/1009034_智能任务详情查询
基础分支: release_20260308

创建结果：
✅ api-service - 成功
✅ web-frontend - 成功

成功: 2/2
```

**步骤 7：开发完成后**

```bash
/tapd-lite complete
```

选择"从当前分支提取"需求ID，确认完成开发：
```
✅ 开发完成：

需求: [1009034] 智能任务详情查询
状态: 开发中 → 完成开发

下一步：
- 提交代码并推送到远程仓库
- 通知测试人员进行测试
```

## 许可证

MIT

