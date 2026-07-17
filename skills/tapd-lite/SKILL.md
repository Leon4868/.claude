---
name: tapd-lite
description: TAPD 轻量级需求管理工具，支持查询需求、开发工作流（开始开发/更新状态/完成开发）、智能生成分支名称、多项目分支创建
---

# TAPD Lite - 轻量级需求管理工具

## ⚠️ 重要：依赖检查

**首次使用前，必须检查并安装依赖：**

```bash
cd "<skill_dir>" && python scripts/check_dependencies.py --install
```

如果依赖缺失，脚本会自动安装 `pyyaml`。

## ⚠️ 重要：交互式执行规范

**本 skill 的所有功能都使用 AskUserQuestion 工具进行交互式操作。**

Claude 在执行时必须：
1. 使用 AskUserQuestion 让用户选择要执行的操作
2. 根据用户选择调用相应的 Python 脚本
3. 在需要用户确认或输入时，使用 AskUserQuestion 获取用户反馈
4. 不要直接执行命令，始终先询问用户

## 参数处理

### 快捷命令支持

当用户使用 `/tapd-lite <command>` 格式时，Claude 应该：

1. **识别命令参数**：
   - `init` → 执行配置初始化
   - `my` → 查询我的需求
   - `export <short_id>` → 导出需求详情 Markdown 到配置的需求文档目录（例如：`/tapd-lite export 1009034`）
   - `start` → 开始开发
   - `complete` → 完成开发
   - 无参数 → 显示主菜单

2. **执行对应功能**：
   - 直接调用相应的脚本，跳过主菜单
   - 仍然使用 AskUserQuestion 进行必要的交互确认

3. **示例**：
   ```
   用户输入：/tapd-lite my
   Claude 行为：直接调用 query_stories.py my，显示需求列表

   用户输入：/tapd-lite export 1009034
   Claude 行为：直接调用 export_story_md.py 1009034 --output-dir "<requirements_dir>"，在配置的需求文档目录生成需求详情 Markdown 文件

   用户输入：/tapd-lite init
   Claude 行为：执行配置初始化流程（步骤 0）

   用户输入：/tapd-lite
   Claude 行为：显示主菜单，让用户选择功能
   ```

## 功能概览

### 需求查询
- 查询我的需求列表
- 生成需求详情
- 查询指定处理人和版本的需求列表

### 开发工作流
- 开始开发：更新 TAPD 状态
- 更新需求状态：手动更新 TAPD 状态
- 完成开发：标记需求完成

### 分支管理
- 智能生成分支名称（自动简化 + 用户确认）
- 多项目批量创建分支

## 主入口（交互式）

### 使用方式

```
/tapd-lite
```

不带参数执行时，使用 AskUserQuestion 显示功能菜单。

### 执行流程

**步骤 1：显示主菜单**

使用 AskUserQuestion 显示功能选项：

```json
{
  "questions": [
    {
      "question": "请选择要执行的操作",
      "header": "TAPD 轻量级工具",
      "multiSelect": false,
      "options": [
        {
          "label": "配置初始化",
          "description": "首次使用时配置用户信息和路径"
        },
        {
          "label": "查询我的需求",
          "description": "查询当前用户的所有需求，按状态分组显示"
        },
        {
          "label": "生成需求详情",
          "description": "导出需求详情 Markdown 到配置的需求文档目录，供后续需求分析使用"
        },
        {
          "label": "查询指定条件的需求",
          "description": "按处理人和/或版本查询需求"
        },
        {
          "label": "开始开发",
          "description": "更新 TAPD 状态为开发中"
        },
        {
          "label": "生成分支名称并创建分支",
          "description": "智能生成分支名称并在项目中创建分支"
        },
        {
          "label": "更新需求状态",
          "description": "手动更新 TAPD 需求状态"
        },
        {
          "label": "完成开发",
          "description": "标记需求开发完成"
        }
      ]
    }
  ]
}
```

**步骤 2：根据用户选择执行相应功能**

## 功能详细说明

### 0. 配置初始化（首次使用）

**触发条件**：用户在主菜单选择"配置初始化"或首次使用时

**功能说明**：配置用户信息和路径设置

**执行流程**：

**步骤 1：检查是否已初始化**

```bash
cd "<skill_dir>" && python scripts/init_config.py --check
```

如果已初始化，显示当前配置并询问是否重新配置。

**步骤 2：询问用户信息**

使用 AskUserQuestion 获取配置信息：

```json
{
  "questions": [
    {
      "question": "请输入你的 TAPD 用户名",
      "header": "TAPD 用户名",
      "multiSelect": false,
      "options": [
        {
          "label": "输入用户名",
          "description": "用于查询你的需求，例如：张三"
        }
      ]
    }
  ]
}
```

**步骤 3：询问 Git 用户名缩写**

```json
{
  "questions": [
    {
      "question": "请输入你的 Git 用户名缩写",
      "header": "Git 用户名",
      "multiSelect": false,
      "options": [
        {
          "label": "输入缩写",
          "description": "用于分支名前缀，例如：lwk"
        }
      ]
    }
  ]
}
```

**步骤 4：询问需求文档目录**

```json
{
  "questions": [
    {
      "question": "请输入需求文档存储目录",
      "header": "文档目录",
      "multiSelect": false,
      "options": [
        {
          "label": "使用默认目录",
          "description": "~/tapd-requirements"
        },
        {
          "label": "自定义目录",
          "description": "输入自定义路径"
        }
      ]
    }
  ]
}
```

**步骤 5：询问 TAPD Token**

```json
{
  "questions": [
    {
      "question": "请输入你的 TAPD API Token",
      "header": "TAPD Token",
      "multiSelect": false,
      "options": [
        {
          "label": "输入 Token",
          "description": "用于 TAPD API 认证"
        },
        {
          "label": "稍后配置",
          "description": "跳过此步骤，稍后通过环境变量设置"
        }
      ]
    }
  ]
}
```

**步骤 6：询问 TAPD Cookie（用于下载图片）**

```json
{
  "questions": [
    {
      "question": "请输入你的 TAPD Cookie（用于下载需求中的图片到本地）",
      "header": "TAPD Cookie",
      "multiSelect": false,
      "options": [
        {
          "label": "输入 Cookie",
          "description": "从浏览器复制完整的 Cookie 字符串"
        },
        {
          "label": "稍后配置",
          "description": "跳过此步骤，图片将无法下载到本地"
        },
        {
          "label": "查看获取方法",
          "description": "查看如何从浏览器获取 Cookie"
        }
      ]
    }
  ]
}
```

如果用户选择"查看获取方法"，显示以下说明：

```
获取 TAPD Cookie 的方法：

1. 在 Chrome 浏览器中登录 TAPD (www.tapd.cn)
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 点击任意请求
6. 在 Headers 部分找到 Cookie 字段
7. 复制完整的 Cookie 值（包括所有键值对）

示例格式：
__root_domain_v=.tapd.cn; tapdsession=xxx; t_u=xxx; ...
```

**步骤 7：保存配置并验证**

```bash
cd "<skill_dir>" && python scripts/init_config.py --tapd-username "<username>" --git-username-abbr "<abbr>" --requirements-dir "<dir>" --tapd-token "<token>" --tapd-cookie "<cookie>"
```

如果用户选择"稍后配置"某些选项，则不传递相应参数：

```bash
# 只配置基本信息
cd "<skill_dir>" && python scripts/init_config.py --tapd-username "<username>" --git-username-abbr "<abbr>" --requirements-dir "<dir>"

# 配置 Token 但不配置 Cookie
cd "<skill_dir>" && python scripts/init_config.py --tapd-username "<username>" --git-username-abbr "<abbr>" --requirements-dir "<dir>" --tapd-token "<token>"
```

脚本会自动执行配置验证，输出格式：
```
SUCCESS=true
TAPD_USERNAME=张三
GIT_USERNAME_ABBR=zs
REQUIREMENTS_DIR=~/tapd-requirements
TAPD_TOKEN=configured
TAPD_COOKIE=configured

Verifying configuration...
User Config: ✓ User configuration is valid
TAPD Token: ✓ TAPD token is set
```

**步骤 8：输出结果**

```
✅ 配置初始化完成：

TAPD 用户名: 张三
Git 用户名缩写: zs
需求文档目录: ~/tapd-requirements
TAPD Token: 已配置
TAPD Cookie: 已配置（可下载图片到本地）

现在可以开始使用 /tapd-lite 的其他功能了！
```

### 1. 查询我的需求

**触发条件**：用户在主菜单选择"查询我的需求"

**执行流程**：
1. 自动计算默认版本号（基于当前日期）：
   - 如果今天是周一到周四：使用本周四的日期
   - 如果今天是周五到周日：使用下周四的日期
   - 格式：YYYY-MMDD（例如：2026-0312）
2. 直接调用脚本查询需求（使用配置文件中的用户名和自动计算的版本）
   ```bash
   cd "<skill_dir>" && python scripts/query_stories.py my
   ```
3. 如果需要指定其他版本，可以使用 `--version` 参数：
   ```bash
   cd "<skill_dir>" && python scripts/query_stories.py my --version "2026-0319"
   ```
4. 显示查询结果（按状态分组）

**输出示例**:
```
查询条件: 处理人=张三, 版本=2026-0312
你的需求（共 4 个）：

开发中（2个）：
  [1009034] 智能任务详情查询 (状态: 开发中, 优先级: 4)
  [1008977] 智能任务策略模板 (状态: 开发中, 优先级: 4)

需求完成（2个）：
  [1009043] 智能任务统计分析 (状态: 需求完成, 优先级: 4)
  ...
```

**说明**：
- 显示的 ID 为 short_id（7位数字），例如 `1009034`
- 完整 ID 为 19 位，例如 `1135238004001009034`
- 用户可以使用 short_id 或完整 ID 进行后续操作

### 2. 生成需求详情（导出 Markdown）

**触发条件**：用户在主菜单选择"导出需求详情"，或使用 `/tapd-lite export <id>`

**功能说明**：在配置的需求文档目录生成完整的需求详情 Markdown 文件，供后续需求分析使用。

**执行流程**：

**步骤 1：询问需求ID**

使用 AskUserQuestion 获取需求ID：

```json
{
  "questions": [
    {
      "question": "请输入需求ID（支持 short_id 或完整 ID）",
      "header": "生成需求详情",
      "multiSelect": false,
      "options": [
        {
          "label": "输入需求ID",
          "description": "例如：1009034（short_id）或 1135238004001009034（完整ID）"
        }
      ]
    }
  ]
}
```

**步骤 2：调用导出脚本生成 Markdown 文件**

在配置的需求文档目录下生成需求详情 Markdown（从 user_config.yaml 读取 requirements_dir）：

```bash
cd "<skill_dir>" && python scripts/export_story_md.py <story_id> --output-dir "<requirements_dir>"
```

其中 `<requirements_dir>` 为用户配置的需求文档目录（user_config.yaml 中的 paths.requirements_dir）。

脚本输出格式：
```
SUCCESS=true
STORY_ID=1135238004001009034
SHORT_ID=1009034
STORY_NAME=智能任务详情查询
OUTPUT_FILE=/path/to/requirements_dir/智能任务详情查询.md
FILE_SIZE=2048
```

**步骤 3：输出结果**

```
✅ 需求详情已导出：

需求: [1009034] 智能任务详情查询
文件: <requirements_dir>/智能任务详情查询.md

后续可直接读取该文件进行需求分析。
```

**生成的 Markdown 文件内容示例**：
```markdown
# 智能任务详情查询

**需求ID**: 1009034 (完整ID: 1135238004001009034)
**状态**: developing
**负责人**: 连武坤
**优先级**: 4
**版本**: 2026-0315
**创建时间**: 2026-03-05 15:23:03
**修改时间**: 2026-03-07 10:07:34

---

## 需求描述

需求背景：...
```

### 3. 查询指定条件的需求

**触发条件**：用户在主菜单选择"查询指定条件的需求"

**执行流程**：

**步骤 1：询问查询条件**

使用 AskUserQuestion 获取查询条件：

```json
{
  "questions": [
    {
      "question": "请选择查询条件",
      "header": "查询条件",
      "multiSelect": false,
      "options": [
        {
          "label": "按处理人查询",
          "description": "输入处理人姓名"
        },
        {
          "label": "按版本查询",
          "description": "输入版本号（如：2026-0315）"
        },
        {
          "label": "按处理人和版本查询",
          "description": "同时指定处理人和版本"
        }
      ]
    }
  ]
}
```

**步骤 2：根据选择获取具体参数**

如果选择"按处理人查询"：
```json
{
  "questions": [
    {
      "question": "请输入处理人姓名",
      "header": "处理人",
      "multiSelect": false,
      "options": [
        {
          "label": "输入姓名",
          "description": "例如：张三"
        }
      ]
    }
  ]
}
```

如果选择"按版本查询"：
```json
{
  "questions": [
    {
      "question": "请输入版本号",
      "header": "版本",
      "multiSelect": false,
      "options": [
        {
          "label": "输入版本号",
          "description": "例如：2026-0315"
        }
      ]
    }
  ]
}
```

如果选择"按处理人和版本查询"：依次询问处理人和版本

**步骤 3：调用脚本查询**

```bash
cd "<skill_dir>" && python scripts/query_stories.py query --owner <owner> --version <version>
```

**输出示例**：
```
查询条件: 处理人: 张三, 版本: 2026-0315
找到 5 个需求：

  [1009034] 智能任务详情查询 (状态: 开发中, 优先级: 4)
    版本: 2026-0315

  [1009035] 智能任务策略模板 (状态: 规划中, 优先级: 4)
    版本: 2026-0315
```

### 4. 开始开发（交互式）

**触发条件**：用户在主菜单选择"开始开发"

**功能说明**：
- 查询待开发需求列表，让用户选择
- 更新 TAPD 状态为"开发中"

**执行流程**：

**步骤 1：查询待开发需求**

调用脚本查询需求（使用配置文件中的用户名）：
```bash
cd "<skill_dir>" && python scripts/query_stories.py my
```

**步骤 2：显示需求列表供选择**

使用 AskUserQuestion 让用户选择需求：

```json
{
  "questions": [
    {
      "question": "请选择要开发的需求",
      "header": "开始开发",
      "multiSelect": false,
      "options": [
        {
          "label": "[1009034] 智能任务详情查询",
          "description": "状态: 规划中, 优先级: 4"
        },
        {
          "label": "[1009035] 智能任务策略模板",
          "description": "状态: 规划中, 优先级: 4"
        },
        {
          "label": "手动输入需求ID",
          "description": "输入其他需求的ID"
        }
      ]
    }
  ]
}
```

**步骤 3：更新状态**

调用脚本更新状态为 `developing`：
```bash
cd "<skill_dir>" && python scripts/update_status.py <story_id> developing
```

**步骤 4：输出结果**

```
✅ 开始开发：

需求: [1009034] 智能任务详情查询
状态: 已更新为"开发中"
```

### 5. 更新需求状态（交互式）

**触发条件**：用户在主菜单选择"更新需求状态"

**功能说明**：手动更新指定需求的 TAPD 状态

**执行流程**：

**步骤 1：询问需求ID**

使用 AskUserQuestion 获取需求ID：

```json
{
  "questions": [
    {
      "question": "请输入需求ID（支持 short_id 或完整 ID）",
      "header": "更新需求状态",
      "multiSelect": false,
      "options": [
        {
          "label": "输入需求ID",
          "description": "例如：1009034（short_id）或 1135238004001009034（完整ID）"
        }
      ]
    }
  ]
}
```

**步骤 2：显示状态选项**

使用 AskUserQuestion 让用户选择目标状态：

```json
{
  "questions": [
    {
      "question": "请选择目标状态\n\n当前需求: [1009034] 智能任务详情查询\n当前状态: 规划中",
      "header": "选择状态",
      "multiSelect": false,
      "options": [
        {
          "label": "开发中 (developing)",
          "description": "正在开发"
        },
        {
          "label": "完成开发 (resolved)",
          "description": "开发完成，待测试"
        },
        {
          "label": "测试中 (status_6)",
          "description": "正在测试"
        },
        {
          "label": "测试通过 (status_4)",
          "description": "测试通过"
        },
        {
          "label": "已上线 (status_3)",
          "description": "已发布到生产环境"
        }
      ]
    }
  ]
}
```

**步骤 3：更新状态**

调用脚本更新状态：
```bash
cd "<skill_dir>" && python scripts/update_status.py <story_id> <status>
```

脚本输出格式：
```
STORY_ID=1135238004001009034
STORY_NAME=智能任务详情查询
OLD_STATUS=planning
OLD_STATUS_NAME=规划中
NEW_STATUS=developing
NEW_STATUS_NAME=开发中
SUCCESS=true
```

**步骤 4：输出结果**

```
✅ 状态更新成功：

需求: [1009034] 智能任务详情查询
原状态: 规划中
新状态: 开发中
```

**状态映射表**：

| 状态值 | 状态名称 | 说明 |
|--------|---------|------|
| `status_1` | 需求中 | 需求初始状态 |
| `planning` | 需求完成 | 需求评审完成 |
| `audited` | 已评审 | 需求已评审 |
| `developing` | 开发中 | 正在开发 |
| `resolved` | 完成开发 | 开发完成，待测试 |
| `status_2` | 已测试 | 测试完成 |
| `status_3` | 已上线 | 已发布到生产环境 |
| `rejected` | 已挂起 | 需求被挂起 |
| `status_4` | 测试通过 | 测试通过 |
| `status_5` | 可上线 | 可以上线 |
| `status_6` | 测试中 | 正在测试 |

### 6. 完成开发（交互式）

**触发条件**：用户在主菜单选择"完成开发"

**功能说明**：标记需求开发完成，更新 TAPD 状态为"完成开发"

**执行流程**：

**步骤 1：询问需求ID**

使用 AskUserQuestion 获取需求ID（或从当前 Git 分支自动提取）：

```json
{
  "questions": [
    {
      "question": "请输入需求ID",
      "header": "完成开发",
      "multiSelect": false,
      "options": [
        {
          "label": "输入需求ID",
          "description": "例如：1135238004001009034"
        },
        {
          "label": "从当前分支提取",
          "description": "从当前 Git 分支名称中提取需求ID"
        }
      ]
    }
  ]
}
```

如果用户选择"从当前分支提取"，调用脚本：

```bash
cd "<skill_dir>" && python scripts/extract_story_id.py
```

脚本输出格式：
```
BRANCH_NAME=lwk/feature/1009034_智能任务详情查询
SHORT_ID=1009034
FULL_ID=1135238004001009034
SUCCESS=true
```

如果提取失败，提示用户手动输入需求ID。

**步骤 2：查询需求详情并确认**

查询需求详情：
```bash
cd "<skill_dir>" && python scripts/query_stories.py detail --story-id <story_id>
```

使用 AskUserQuestion 显示需求信息并确认：

```json
{
  "questions": [
    {
      "question": "确认完成开发？\n\n需求信息：\n- ID: 1135238004001009034\n- 标题: 智能任务详情查询\n- 当前状态: 开发中\n- 优先级: 4",
      "header": "完成开发",
      "multiSelect": false,
      "options": [
        {
          "label": "确认完成",
          "description": "标记需求为已完成，更新 TAPD 状态"
        },
        {
          "label": "继续开发",
          "description": "保持当前状态，继续开发"
        }
      ]
    }
  ]
}
```

**步骤 3：更新状态**

调用脚本更新状态为 `resolved`：
```bash
cd "<skill_dir>" && python scripts/update_status.py <story_id> resolved
```

**步骤 4：输出结果**

```
✅ 开发完成：

需求: [1009034] 智能任务详情查询
状态: 开发中 → 完成开发

下一步：
- 提交代码并推送到远程仓库
- 通知测试人员进行测试
```

### 7. 生成分支名称并创建分支（交互式）

**触发条件**：用户在主菜单选择"生成分支名称并创建分支"

**执行流程**：

**步骤 1：询问需求ID**

使用 AskUserQuestion 获取需求ID：

```json
{
  "questions": [
    {
      "question": "请输入需求ID（支持 short_id 或完整 ID）",
      "header": "生成分支名称",
      "multiSelect": false,
      "options": [
        {
          "label": "输入需求ID",
          "description": "例如：1009034（short_id）或 1135238004001009034（完整ID）"
        }
      ]
    }
  ]
}
```

**步骤 2：获取故事信息并生成建议名称**

调用脚本获取故事信息：
```bash
cd "<skill_dir>" && python scripts/generate_branch.py <story_id>
```

脚本输出格式（键值对）:
```
FULL_ID=1135238004001009034
SHORT_ID=1009034
STORY_NAME=智能任务策略模板条件支持有效接通次数统计
STORY_NAME_SHORT=智能任务策略模板条件有效接通次数
VERSION=2026-0315
BRANCH_NAME=lwk/feature/1009034_智能任务策略模板条件有效接通次数
NAME_SIMPLIFIED=true
```

**步骤 3：显示建议名称并询问用户确认**

使用 AskUserQuestion 显示建议名称：

```json
{
  "questions": [
    {
      "question": "请确认分支名称\n\n故事信息：\n- 完整ID: 1135238004001009034\n- 短ID: 1009034\n- 原始名称: 智能任务策略模板条件支持有效接通次数统计\n- 简化名称: 智能任务策略模板条件有效接通次数\n- 版本: 2026-0315\n\n建议的分支名称：\nlwk/feature/1009034_智能任务策略模板条件有效接通次数",
      "header": "确认分支名称",
      "multiSelect": false,
      "options": [
        {
          "label": "使用建议名称",
          "description": "确认使用上述分支名称"
        },
        {
          "label": "自定义名称",
          "description": "手动输入故事名称（≤21字符）"
        },
        {
          "label": "取消",
          "description": "取消生成分支名称"
        }
      ]
    }
  ]
}
```

**步骤 4：如果用户选择"自定义名称"**

使用 AskUserQuestion 获取自定义名称：

```json
{
  "questions": [
    {
      "question": "请输入自定义的故事名称（建议 ≤21 字符）\n\n原始名称: 智能任务策略模板条件支持有效接通次数统计\n建议简化: 智能任务策略模板条件有效接通次数",
      "header": "自定义名称",
      "multiSelect": false,
      "options": [
        {
          "label": "输入自定义名称",
          "description": "例如：智能任务策略模板"
        }
      ]
    }
  ]
}
```

然后使用自定义名称重新生成：

```bash
cd "<skill_dir>" && python scripts/generate_branch.py <story_id> --custom-name "<custom_name>"
```

**步骤 5：选择要创建分支的项目**

使用 AskUserQuestion 询问项目范围：

```json
{
  "questions": [
    {
      "question": "请选择要创建分支的项目范围",
      "header": "选择项目",
      "multiSelect": false,
      "options": [
        {
          "label": "仅当前项目",
          "description": "只在当前项目中创建分支"
        },
        {
          "label": "多个项目",
          "description": "在多个项目中创建分支"
        },
        {
          "label": "仅生成分支名称",
          "description": "不创建分支，只输出分支名称"
        }
      ]
    }
  ]
}
```

**步骤 6a：如果选择"仅当前项目"**

首先查找基础分支：

```bash
cd "<skill_dir>" && python scripts/find_base_branch.py --project-path .
```

脚本输出格式：
```
BASE_BRANCH=release_20260308
COMMIT_TIME=1709884800
COMMIT_TIME_STR=2026-03-08 10:00:00
PATTERN=^release_20\d{6}$
SORT_BY=both
```

如果找不到匹配的分支，使用 AskUserQuestion 询问用户：

```json
{
  "questions": [
    {
      "question": "未找到匹配的基础分支（release_20*），请选择基础分支",
      "header": "选择基础分支",
      "multiSelect": false,
      "options": [
        {
          "label": "develop",
          "description": "使用 develop 分支"
        },
        {
          "label": "main",
          "description": "使用 main 分支"
        },
        {
          "label": "master",
          "description": "使用 master 分支"
        },
        {
          "label": "手动输入",
          "description": "输入其他分支名称"
        }
      ]
    }
  ]
}
```

然后在当前项目创建分支：

```bash
git fetch --all
git checkout -b <branch_name> origin/<base_branch>
```

输出结果：
```
✅ 分支已创建：

项目: current-project
分支名称: lwk/feature/1009034_智能任务策略模板条件有效接通次数
基础分支: release_20260308
状态: 成功
```

**步骤 6b：如果选择"多个项目"**

首先扫描父目录下的所有 Git 项目：

```bash
cd "<skill_dir>" && python scripts/scan_projects.py
```

脚本输出格式：
```
BASE_DIR=/path/to/parent
CURRENT_DIR=/path/to/parent/current-project
CURRENT_PROJECT=current-project
TOTAL_PROJECTS=5
PROJECTS_START
ai-decision-system|/path/to/parent/ai-decision-system
data-center|/path/to/parent/data-center
task-service|/path/to/parent/task-service
user-service|/path/to/parent/user-service
web-frontend|/path/to/parent/web-frontend
PROJECTS_END
```

然后使用 AskUserQuestion 让用户选择项目（支持多选）：

```json
{
  "questions": [
    {
      "question": "请选择要创建分支的项目（可多选）\n\n当前项目: current-project\n父目录: /path/to/parent\n\n找到 5 个 Git 项目：",
      "header": "选择项目",
      "multiSelect": true,
      "options": [
        {
          "label": "ai-decision-system",
          "description": "/path/to/parent/ai-decision-system"
        },
        {
          "label": "data-center",
          "description": "/path/to/parent/data-center"
        },
        {
          "label": "task-service",
          "description": "/path/to/parent/task-service"
        },
        {
          "label": "user-service",
          "description": "/path/to/parent/user-service"
        },
        {
          "label": "web-frontend",
          "description": "/path/to/parent/web-frontend"
        }
      ]
    }
  ]
}
```

**步骤 7：在选中的项目中创建分支**

调用脚本在多个项目中创建分支（自动查找基础分支，显示进度）：

```bash
cd "<skill_dir>" && python scripts/create_branches.py "<branch_name>" --projects "/path/to/project1" "/path/to/project2" --show-progress
```

脚本会在 stderr 输出进度信息：
```
Processing 1/3: ai-decision-system...
  ✓ Branch created successfully from release_20260308
Processing 2/3: data-center...
  ✓ Branch created successfully from release_20260308
Processing 3/3: task-service...
  ✗ Branch already exists
```

最终输出格式（stdout）：
```
BRANCH_NAME=lwk/feature/1009034_智能任务策略模板条件有效接通次数
TOTAL_PROJECTS=3
RESULTS_START
ai-decision-system|SUCCESS|Branch created successfully from release_20260308 (base: release_20260308)
data-center|SUCCESS|Branch created successfully from release_20260308 (base: release_20260308)
task-service|FAILED|Branch already exists: lwk/feature/1009034_智能任务策略模板条件有效接通次数 (base: release_20260308)
RESULTS_END
```

**如果找不到基础分支**：

调用脚本查找基础分支时添加 `--show-fallback` 参数：

```bash
cd "<skill_dir>" && python scripts/find_base_branch.py --project-path . --show-fallback
```

输出会包含后备分支和所有可用分支列表：
```
PATTERN=^release_20\d{6}$
BASE_BRANCH=
ERROR=No matching branch found
FALLBACK=develop
TOTAL_BRANCHES=15
ALL_BRANCHES_START
develop
main
master
feature/task-123
...
ALL_BRANCHES_END
```

然后使用 AskUserQuestion 让用户选择基础分支：

```json
{
  "questions": [
    {
      "question": "未找到匹配的基础分支（release_20*），请选择基础分支\n\n可用分支：\n- develop\n- main\n- master\n...",
      "header": "选择基础分支",
      "multiSelect": false,
      "options": [
        {
          "label": "develop",
          "description": "使用 develop 分支（推荐）"
        },
        {
          "label": "main",
          "description": "使用 main 分支"
        },
        {
          "label": "master",
          "description": "使用 master 分支"
        },
        {
          "label": "手动输入",
          "description": "输入其他分支名称"
        }
      ]
    }
  ]
}
```

**步骤 8：输出最终结果**

```
✅ 分支创建完成：

分支名称: lwk/feature/1009034_智能任务策略模板条件有效接通次数

创建结果：
✅ ai-decision-system - 成功
✅ data-center - 成功
❌ task-service - 失败：分支已存在

成功: 2/3
失败: 1/3
```

**步骤 6c：如果选择"仅生成分支名称"**

只输出分支名称，不创建分支：

```
✅ 分支名称已生成：

lwk/feature/1009034_智能任务策略模板条件有效接通次数

可以使用以下命令手动创建分支：
git checkout -b lwk/feature/1009034_智能任务策略模板条件有效接通次数
```

## 技术说明

### 分支名称生成规则

格式：`{username_abbr}/feature/{short_id}_{story_name_short}`

**Short ID 提取规则**：
- 从完整的 story_id 中提取后7位作为 short_id
- 例如：`1135238004001009034` → `1009034`

**标题简化算法**：
1. 如果标题 ≤ 21 字符，直接使用
2. 如果标题 > 21 字符：
   - 提取关键词（去除"支持"、"实现"、"优化"等动词）
   - 保留核心名词（如"智能任务"、"策略模板"）
   - 截取前 21 字符

示例：
- "智能任务详情查询" → "智能任务详情查询"（8字符，保持原样）
- "智能任务策略模板条件支持有效接通次数统计" → "智能任务策略模板条件有效接通次数"（提取核心）
- "新版智能任务要覆盖的企业特殊配置" → "新版智能任务企业特殊配置"（提取核心）

完整示例：
- 完整ID: `1135238004001009034` → 分支名: `lwk/feature/1009034_智能任务详情查询`
- 完整ID: `1135238004001009035` → 分支名: `lwk/feature/1009035_智能任务策略模板条件有效接通次数`

### 基础分支查找规则

**查找流程**：
1. 执行 `git fetch --all` 获取最新的远程分支
2. 使用正则表达式匹配分支名称（默认：`^release_20\d{6}$`）
3. 按照配置的排序规则选择最新分支：
   - `name`：按分支名称字典序排序（降序）
   - `commit_time`：按最后提交时间排序（降序）
   - `both`：优先按分支名称排序，名称相同则按提交时间

**示例**：
- 匹配的分支：`release_20260308`, `release_20260301`, `release_20260215`
- 排序结果：`release_20260308`（最新）

**后备方案**：
- 如果找不到匹配的分支，使用配置文件中的 `fallback` 分支（默认：`develop`）
- 或通过 AskUserQuestion 询问用户选择基础分支

### API 认证

使用 Bearer token 认证：
```
Authorization: Bearer {TAPD_TOKEN}
```

## 配置

### 首次使用

首次使用时需要运行配置初始化：

```
/tapd-lite
```

选择"配置初始化"，按提示输入：
1. TAPD 用户名（用于查询需求）
2. Git 用户名缩写（用于分支名前缀）
3. 需求文档目录（默认：~/tapd-requirements）

### 环境变量

- `TAPD_TOKEN`：TAPD API 认证 token（必需）
- `GIT_USERNAME_ABBR`：Git 用户名缩写（可选，优先使用配置文件中的值）

### 配置文件

配置文件位于 `config/` 目录：

**tapd_config.yaml**：TAPD API 配置
- `base_url`：TAPD API 地址
- `workspace_id`：工作空间 ID
- `status_map`：状态映射表

**git_config.yaml**：Git 分支配置
- `username_abbr`：用户名缩写
- `branch_format`：分支命名格式
- `max_story_name_length`：故事名称最大长度
- `base_branch`：基础分支配置
  - `pattern`：分支名称匹配正则表达式（默认：`^release_20\d{6}$`）
  - `fallback`：后备分支（默认：`develop`）
  - `sort_by`：排序规则（`name`/`commit_time`/`both`）

**user_config.yaml**：用户个人配置
- `user.tapd_username`：TAPD 用户名
- `user.git_username_abbr`：Git 用户名缩写
- `user.tapd_cookie`：TAPD 浏览器 Cookie（可选，用于下载需求图片到本地）
- `paths.requirements_dir`：需求文档目录

### 快捷命令

支持以下快捷命令：

```bash
/tapd-lite init              # 配置初始化
/tapd-lite my                # 查询我的需求
/tapd-lite export <short_id> # 导出需求详情 Markdown（例如：/tapd-lite export 1009034）
/tapd-lite start             # 开始开发
/tapd-lite complete          # 完成开发
```

## 注意事项

1. **首次使用**：运行 `/tapd-lite` 选择"配置初始化"进行配置（包括 TAPD Token 和 Cookie）
2. **图片下载**：配置 TAPD Cookie 后可将需求中的图片下载到本地，未配置时图片引用本地路径但文件为占位符
3. **分支命名**：格式为 `{username_abbr}/feature/{short_id}_{story_name_short}`
4. **基础分支**：自动查找 `release_20*` 格式的最新分支，找不到时使用后备分支
5. **交互式操作**：所有操作都通过 AskUserQuestion 进行交互式确认
6. **错误重试**：网络请求失败时自动重试最多 3 次
7. **Git 操作**：创建分支前会自动执行 `git fetch --all` 获取最新远程分支
