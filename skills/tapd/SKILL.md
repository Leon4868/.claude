---
name: tapd
description: TAPD 需求管理工具，支持创建需求、查询需求、开始开发（生成文档和分支名）、创建分支、查看当前任务、完成开发等完整开发流程。
---

# TAPD 需求管理

## ⚠️ 最高优先级：先规划后实现原则

**🚫 禁止在用户确认方案前编写代码！**

执行 `/tapd start` 后的正确流程：
1. ✅ 阅读 `requirement.md` 理解需求
2. ✅ 在 `implementationPlan.md` 中详细规划实现方案
3. ✅ 在 `development.md` 中填写涉及的项目列表
4. ✅ **明确询问用户是否确认方案**
5. ✅ 用户确认后，再使用 `/tapd create-branch` 创建分支
6. ✅ 最后才开始编写代码

**违反此原则将导致返工和浪费时间！**

## ⚠️ 重要：开发分支规范

**修改代码时，必须在对应的开发分支上进行。** 在修改任何代码文件之前，先检查当前分支是否为该需求的开发分支，如果不是，必须先切换到正确的开发分支再进行修改。

**从 release 分支创建开发分支时，默认必须基于符合 `release_20*` 规则的最新 release 分支拉取代码。**
- 正确做法：先 `git fetch --all`，自动识别最新 release 分支，切到该分支并拉取最新代码，再从当前 HEAD 创建开发分支
- 找不到匹配的 release 分支时，才允许回退到 fallback 分支（默认 `develop`）
- 错误做法：使用过期的 release 分支，或直接基于本地旧代码创建开发分支

## ⚠️ 重要：文档同步规范

**修改代码后，必须同步检查需求文档目录下的以下文件是否需要更新：**
- `development.md` - 开发进度、代码提交记录
- `implementationPlan.md` - 实现方案、修改文件清单
- `release.md` - 发版文档、SQL 变更、验证方案
- `requirement.md` - 需求规格、接口变更

## ⚠️ 重要：Python 脚本执行规范

**执行 Python 脚本时，必须遵循以下规范：**

1. **路径处理**（跨平台通用）：
   - **始终使用双引号包裹路径**，无论是 Windows、Linux 还是 macOS
   - 这样可以正确处理包含空格的路径，并避免特殊字符被 shell 解释
   - 技能基础目录变量：使用 `"${SKILL_BASE_DIR}"` 或直接使用完整路径

2. **推荐的命令格式**：
   ```bash
   cd "${SKILL_BASE_DIR}" && python scripts/workflow/脚本名.py --参数
   ```
   或
   ```bash
   cd "完整路径" && python scripts/workflow/脚本名.py --参数
   ```

3. **示例**（跨平台）：
   ```bash
   # Windows ✓
   cd "C:\Users\54542\.claude\skills\tapd" && python scripts/workflow/query_stories.py --mode my

   # Linux/macOS ✓
   cd "/home/user/.claude/skills/tapd" && python scripts/workflow/query_stories.py --mode my
   cd "$HOME/.claude/skills/tapd" && python scripts/workflow/query_stories.py --mode my

   # 错误示例 ✗（不带引号）
   cd C:\Users\54542\.claude\skills\tapd && python scripts/workflow/query_stories.py --mode my
   cd /home/user/.claude/skills/tapd && python scripts/workflow/query_stories.py --mode my
   ```

4. **为什么需要引号**：
   - Windows：反斜杠 `\` 会被 bash 解释为转义字符
   - Linux/macOS：路径中的空格会导致命令解析错误
   - 所有平台：特殊字符（如 `$`、`~`、`&` 等）可能被 shell 解释

## 开发工作流程

完整的开发流程如下：

1. **初始化配置**（首次使用）- 配置环境变量
   ```
   /tapd init
   ```
   - 引导用户设置必要的环境变量（`CODE_ROOT_DIR`、`TAPD_TOKEN` 等）
   - 验证环境变量是否生效

2. **查询需求** - 查看待开发的需求列表
   ```
   /tapd
   ```
   - 交互式选择查询模式：我的需求、本周需求、需求详情
   - 或直接使用 `/tapd my` 或 `/tapd week`

3. **开始开发** - 创建需求文档，生成建议分支名
   ```
   /tapd start
   ```
   - 自动列出待开发需求供选择
   - 创建需求文档目录和模板文件
   - 更新 TAPD 状态为 `developing`
   - ⚠️ **此时不要立即编写代码，先进行需求分析和方案规划**

4. **需求分析与方案规划** - ⚠️ **必须先完成此步骤，再创建分支和编写代码**
   - 阅读 `requirement.md`，理解需求背景和目标
   - 分析涉及的服务、模块、表、接口等
   - 在 `implementationPlan.md` 中详细规划实现方案：
     - 整体思路和技术选型
     - 涉及的文件清单和修改内容
     - 实现步骤和测试计划
   - 在 `development.md` 中填写涉及的项目列表
   - **等待用户确认方案后再继续**

5. **创建分支** - 方案确认后创建开发分支
   ```
   /tapd create-branch
   ```
   - 显示涉及的项目列表
   - 确认分支名称
   - 创建并切换到新分支

6. **编写代码** - 按照实现方案编写代码，使用 `/commit-cn` 提交代码

7. **完成开发** - 标记需求完成
   ```
   /tapd complete
   ```
   - 显示需求信息
   - 确认是否完成开发
   - 更新 TAPD 状态为 `resolved`

8. **生成发版文档** - 自动生成发版文档（会读取 `development.md` 中的项目信息）
   ```
   /release-doc-generator
   ```

**重要提示**：
1. **严格遵循"先规划后实现"原则**：执行 `/tapd start` 后，必须先完成需求分析和方案规划，等待用户确认后再创建分支和编写代码
2. **禁止跳过规划步骤**：不要在用户确认方案前就开始编写代码，这可能导致返工
3. **需求分析要点**：
   - 理解需求背景和目标
   - 规划涉及的服务、模块、表、接口等
   - 将实现计划详细记录到 `implementationPlan.md`
   - 在 `development.md` 中填写涉及的项目列表
4. **等待确认**：完成规划后，明确询问用户是否确认方案，确认后再继续

## 功能

### 0. 初始化配置 (`init`)

首次使用时引导用户配置环境变量。

**使用方式**：
```
/tapd init
```

**执行流程**：
1. 使用 AskUserQuestion 询问代码根目录路径
2. 引导用户设置环境变量 `CODE_ROOT_DIR`
3. 验证环境变量是否生效

**交互示例**：
```
问题: "请输入代码根目录路径"
选项:
1. "使用当前目录" - 使用当前工作目录作为代码根目录
2. "自定义路径" - 手动输入代码根目录路径
```

**设置方式**：
```bash
# Windows（永久生效）
setx CODE_ROOT_DIR "D:\Code"

# Linux/Mac（添加到 ~/.bashrc 或 ~/.zshrc）
export CODE_ROOT_DIR="/home/user/code"
```

### 1. 查询需求（交互式）

不带参数执行 `/tapd` 时，显示交互式选项让用户选择查询模式。

**使用方式**：
```
/tapd
```

**执行流程**：
1. 使用 AskUserQuestion 显示查询模式选项
2. 根据用户选择执行相应的查询操作

**交互示例**：
```
问题: "请选择查询模式"
选项:
1. "我的需求" - 查询当前用户的所有需求
2. "本周需求" - 查询本周创建或更新的需求
3. "需求详情" - 查询指定需求的详细信息
```

#### 1.1 查询我的需求 (`my`)

查询当前用户的所有需求，按状态分组显示。

**使用方式**：
```
/tapd my
```

**执行流程**：
1. 调用 `python scripts/workflow/query_stories.py --mode my` 查询需求
2. 按状态分组显示需求列表

**示例输出**：
```
你的需求（共 50 个）：

开发中（2个）：
  [1135238004001008977] 智能任务策略模板条件支持有效接通次数 (状态: 开发中, 优先级: 4)
  [1135238004001008757] 新版智能任务要覆盖的企业特殊配置 (状态: 开发中, 优先级: 4)

规划中（8个）：
  [1135238004001009043] 智能任务统计分析增加聚合维度分析 (状态: 规划中, 优先级: 4)
  ...
```

#### 1.2 查询本周需求 (`week`)

查询本周创建或更新的需求。

**使用方式**：
```
/tapd week
```

**执行流程**：
1. 计算本周日期范围（周一到周日）
2. 调用 `python scripts/workflow/query_stories.py --mode week` 查询需求
3. 显示本周相关需求列表

**示例输出**：
```
本周范围: 2026-03-02 到 2026-03-08
本周相关需求（共 11 个）：

[创建] [1135238004001008977] 智能任务策略模板条件支持有效接通次数 (状态: 开发中, 优先级: 4)
  时间: 2026-03-02 15:23:03

[更新] [1135238004001009041] 抖店挽单场景结果上报 (状态: 已解决, 优先级: 4)
  时间: 2026-03-04 10:07:34
```

#### 1.3 查询需求详情 (`detail`)

查询指定需求的详细信息。

**使用方式**：
```
/tapd detail {story_id}
```

**执行流程**：
1. 如果未提供 story_id，使用 AskUserQuestion 询问需求 ID
2. 调用 `python scripts/workflow/query_stories.py --mode detail --story-id {story_id}` 查询详情
3. 显示需求详细信息

### 2. 开始开发 (`start`) - 交互式

开始开发一个 TAPD 需求，自动执行以下操作：
- 查询需求列表，让用户选择要开发的需求
- 查询需求详情
- 生成建议的分支名称（格式：`lwk/feature_{需求名称}_{需求ID}_{版本时间}`）
- 创建需求文档目录（`~/tapd-requirements/{需求ID}_{需求名称}_{版本时间}/`）
- 生成需求文档：
  - `requirement.md` - 需求原文（从 TAPD 获取）
  - `development.md` - 开发信息（分支名称、涉及项目列表）
  - `implementationPlan.md` - 实现计划模板
  - `release.md` - 发版文档模板
  - `claude.md` - Claude Code 项目上下文文档
- 更新 TAPD 状态为 `developing`

**使用方式**：
```
/tapd start
```

**执行流程**：
1. 调用 `python scripts/workflow/query_stories.py --mode my` 查询待开发需求
2. 使用 AskUserQuestion 显示需求列表，让用户选择要开发的需求
3. 调用 `python scripts/workflow/start_dev.py --story-id {story_id}` 执行开发准备流程
   - **如果需求文档目录已存在**，脚本会抛出 `FileExistsError` 异常
   - Claude 捕获异常后，使用 `AskUserQuestion` 询问用户是否覆盖
   - 如果用户选择覆盖，使用 `--force` 参数重新执行：`python scripts/workflow/start_dev.py --story-id {story_id} --force`
4. 显示操作结果和后续步骤提示

**交互示例**：
```
问题: "请选择要开发的需求"
选项:
1. "[1135238004001008977] 智能任务策略模板条件支持有效接通次数" - 状态: 规划中, 优先级: 4
2. "[1135238004001009043] 智能任务统计分析增加聚合维度分析" - 状态: 规划中, 优先级: 4
3. "手动输入需求ID" - 输入其他需求的ID
```

**重要说明**：
- 此命令**不会立即创建分支**，只生成建议的分支名称
- 需要先分析需求，规划具体实现方案
- 在 `development.md` 中填写涉及的项目列表
- 确认涉及项目后，使用 `/tapd create-branch` 创建分支
- **文件覆盖保护**：
  - 如果需求文档目录已存在，脚本会抛出错误并列出已存在的文件
  - Claude 会使用 `AskUserQuestion` 询问用户是否覆盖
  - 用户确认后，使用 `--force` 参数重新执行

**需求分析建议**：
1. 阅读 `requirement.md` 理解需求背景和目标
2. 分析涉及的服务、模块、表、接口等
3. 规划具体实现步骤和代码修改点
4. 将分析结果记录到 `implementationPlan.md`
5. 在 `development.md` 中填写涉及的项目列表

### 3. 创建分支 (`create-branch`) - 交互式

在确认涉及项目后，创建开发分支。

**使用方式**：
```
/tapd create-branch
```

**执行流程**：
1. 从 `development.md` 读取建议的分支名称和涉及的项目列表
2. 使用 AskUserQuestion 显示涉及的项目并确认是否创建分支
3. 调用 `python scripts/workflow/create_branch.py` 创建并切换到新分支
   - 先 `git fetch --all`
   - 自动查找符合 `release_20*` / `^release_20\d{6}$` 规则的**最新 release 分支**作为基线
   - 如果找不到匹配的 release 分支，再回退到配置中的 fallback 分支（默认 `develop`）
   - 切到目标 base/release 分支并拉取最新代码
   - 再从当前 HEAD 创建开发分支
   - **禁止**让新开发分支 tracking 到 release/base 分支
4. 显示操作结果

**交互示例**：
```
问题: "确认创建开发分支？"
涉及的项目：
- ai-decision-system
- data-center

建议的分支名称：lwk/feature_智能任务策略模板条件支持有效接通次数_1135238004001008977_20260315

选项:
1. "确认创建" - 使用建议的分支名称创建分支
2. "修改分支名" - 自定义分支名称后创建
3. "取消" - 取消创建分支
```

**前置条件**：
- 已执行 `/tapd start` 创建需求文档
- 已在 `development.md` 中填写涉及的项目列表

### 4. 更新需求状态 (`update`)

手动更新指定需求的状态。

**使用方式**：
```
/tapd update {story_id} {status}
```

**参数说明**：
- `story_id`：需求 ID（如 1135238004001009076）
- `status`：目标状态值（见下方状态映射表）

**执行流程**：
1. 查询需求当前状态
2. 调用 `python scripts/workflow/update_story_status.py --story-id {story_id} --status {status}` 更新状态
3. 显示更新结果

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
| `workflow_suspended` | 流程挂起 | 工作流挂起 |
| `workflow_end` | 流程终止 | 工作流终止 |

**示例**：
```bash
# 更新为测试中
/tapd update 1135238004001009076 status_6

# 更新为完成开发
/tapd update 1135238004001009076 resolved

# 更新为开发中
/tapd update 1135238004001009076 developing
```

**注意**：
- 状态值必须使用 TAPD API 的实际值（如 `status_6`），而不是显示名称（如"测试中"）
- 可以通过 `/tapd my` 查看需求列表时看到状态的中文名称
- 状态映射关系通过 TAPD API `/workflows/status_map` 接口获取

### 5. 查看当前任务 (`status`)

显示当前正在开发的需求信息。

**使用方式**：
```
/tapd status
```

**执行流程**：
1. 使用 git_helper 获取当前分支
2. 从分支名提取需求 ID
3. 查询需求详情并显示

### 6. 完成开发 (`complete`) - 交互式

标记需求开发完成，更新 TAPD 状态。

**使用方式**：
```
/tapd complete
```

**执行流程**：
1. 获取当前分支的需求 ID
2. 查询需求详情
3. 使用 AskUserQuestion 显示需求信息并确认是否完成开发
4. 更新 TAPD 状态为 `resolved`
5. 显示操作结果

**交互示例**：
```
需求信息：
- ID: 1135238004001008977
- 标题: 智能任务策略模板条件支持有效接通次数
- 当前状态: 开发中
- 优先级: 4

问题: "确认完成开发？"
选项:
1. "确认完成" - 标记需求为已完成，更新 TAPD 状态
2. "继续开发" - 保持当前状态，继续开发
3. "查看详情" - 查看需求详细信息后再决定
```

## 配置

### 配置文件

- `config/tapd_config.yaml` - TAPD API 配置和状态映射
- `config/git_config.yaml` - Git 分支命名规范
- `config/requirement_doc_config.yaml` - 需求文档配置

### 需求文档目录配置

需求文档目录可以通过以下方式配置（优先级从高到低）：

1. **环境变量**：设置 `TAPD_REQUIREMENTS_DIR` 环境变量
   ```bash
   # Windows
   set TAPD_REQUIREMENTS_DIR=D:\MyProjects\tapd-requirements

   # Linux/Mac
   export TAPD_REQUIREMENTS_DIR=~/projects/tapd-requirements
   ```

2. **配置文件默认值**：如果未设置环境变量，使用 `~/tapd-requirements`（用户主目录下的 tapd-requirements 文件夹）

配置文件 `config/requirement_doc_config.yaml` 中的设置：
```yaml
requirement_doc:
  # 需求文档根目录（可通过环境变量 TAPD_REQUIREMENTS_DIR 覆盖）
  root_dir: "${TAPD_REQUIREMENTS_DIR:~/tapd-requirements}"

  # 目录命名格式
  dir_format: "{story_id}_{story_name_short}_{date}"

  # 需求名称最大长度（用于目录名）
  max_name_length: 20
```

**示例**：
- 未设置环境变量：文档保存在 `C:\Users\你的用户名\tapd-requirements\`（Windows）或 `~/tapd-requirements/`（Linux/Mac）
- 设置环境变量：文档保存在你指定的目录

## 技术说明

### 交互式功能实现

本技能使用 `AskUserQuestion` 工具实现交互式功能，提供更友好的用户体验。

#### 1. 初始化配置交互

```json
{
  "questions": [
    {
      "question": "请输入代码根目录路径",
      "header": "代码根目录",
      "multiSelect": false,
      "options": [
        {
          "label": "使用当前目录",
          "description": "使用当前工作目录作为代码根目录"
        },
        {
          "label": "自定义路径",
          "description": "手动输入代码根目录路径"
        }
      ]
    }
  ]
}
```

#### 2. 查询模式选择交互

```json
{
  "questions": [
    {
      "question": "请选择查询模式",
      "header": "查询模式",
      "multiSelect": false,
      "options": [
        {
          "label": "我的需求",
          "description": "查询当前用户的所有需求"
        },
        {
          "label": "本周需求",
          "description": "查询本周创建或更新的需求"
        },
        {
          "label": "需求详情",
          "description": "查询指定需求的详细信息"
        }
      ]
    }
  ]
}
```

#### 3. 开始开发需求选择交互

```json
{
  "questions": [
    {
      "question": "请选择要开发的需求",
      "header": "选择需求",
      "multiSelect": false,
      "options": [
        {
          "label": "[1135238004001008977] 智能任务策略模板条件支持有效接通次数",
          "description": "状态: 规划中, 优先级: 4"
        },
        {
          "label": "[1135238004001009043] 智能任务统计分析增加聚合维度分析",
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

#### 4. 创建分支确认交互

```json
{
  "questions": [
    {
      "question": "确认创建开发分支？\n\n涉及的项目：\n- ai-decision-system\n- data-center\n\n建议的分支名称：lwk/feature_智能任务策略模板条件支持有效接通次数_1135238004001008977_20260305",
      "header": "创建分支",
      "multiSelect": false,
      "options": [
        {
          "label": "确认创建",
          "description": "使用建议的分支名称创建分支"
        },
        {
          "label": "修改分支名",
          "description": "自定义分支名称后创建"
        },
        {
          "label": "取消",
          "description": "取消创建分支"
        }
      ]
    }
  ]
}
```

#### 5. 完成开发确认交互

```json
{
  "questions": [
    {
      "question": "确认完成开发？\n\n需求信息：\n- ID: 1135238004001008977\n- 标题: 智能任务策略模板条件支持有效接通次数\n- 当前状态: 开发中\n- 优先级: 4",
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
        },
        {
          "label": "查看详情",
          "description": "查看需求详细信息后再决定"
        }
      ]
    }
  ]
}
```

### API 认证

所有 TAPD API 调用统一使用 Python 脚本，通过 Bearer token 认证：
- Token 从环境变量 `TAPD_TOKEN` 读取
- 使用 `Authorization: Bearer {token}` 请求头
- 避免了 curl 的 Basic Auth 认证问题

### 中文编码处理

Python 脚本使用 UTF-8 编码，避免 Windows 命令行中文乱码问题：
- 所有输出使用 `print()` 函数，自动处理编码
- JSON 文件使用 `ensure_ascii=False` 保存中文

## 注意事项

1. **TAPD Token**：确保已设置 `TAPD_TOKEN` 环境变量
2. **Git 仓库**：开发流程功能（start/create-branch/status/complete）需要在 Git 仓库中使用
3. **需求文档目录**：
   - 默认保存在 `~/tapd-requirements/`（用户主目录）
   - 可通过环境变量 `TAPD_REQUIREMENTS_DIR` 自定义目录
   - 目录会自动创建，无需手动创建
4. **分支命名规范**：`lwk/feature_{需求名称}_{需求ID}_{版本时间}`
5. **开发信息文档**：
   - `development.md` 记录分支名称和涉及的项目列表
   - 必须在创建分支前填写涉及的项目信息
   - 发版文档生成时会读取此文件中的项目信息
6. **需求分析流程**：
   - 执行 `/tapd start` 后，分析需求并规划实现方案
   - 将实现计划记录到 `implementationPlan.md`
   - 在 `development.md` 中填写涉及的项目列表
   - 完成分析后再执行 `/tapd create-branch` 创建开发分支

## 常见问题与解决方案

### 1. TAPD_TOKEN 环境变量找不到

**问题**：执行脚本时提示 `TAPD token not found`

**原因**：在 Windows 系统上，环境变量可能设置在用户环境变量中，而不是当前 shell 环境

**解决方案**：
```bash
# Windows: 从用户环境变量读取
export TAPD_TOKEN=$(powershell -Command "[System.Environment]::GetEnvironmentVariable('TAPD_TOKEN', 'User')")

# 然后执行脚本
cd "C:\Users\54542\.claude\skills\tapd" && python scripts/workflow/query_stories.py --mode my
```

### 2. 创建需求时的 API 认证

**问题**：创建需求（POST 请求）返回 404 或 401 错误

**原因**：
- Bearer token 认证对 POST 请求同样有效
- 需要正确设置 `Content-Type: application/x-www-form-urlencoded`
- 数据必须放在请求体中，而不是 URL 参数

**正确示例**：
```python
data = urlencode({'workspace_id': '35238004', 'name': '需求名称'}).encode('utf-8')
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/x-www-form-urlencoded'
}
request = Request(url, data=data, headers=headers, method='POST')
```

### 3. 版本号字段混淆

**问题**：设置 `iteration_id` 为日期字符串（如 "20260305"）时返回 404 错误

**原因**：
- `iteration_id` 需要填写实际存在的迭代 ID（如 "1135238004001000012"）
- `version` 字段是文本字段，可以直接填写日期格式（如 "2026-0305"）

**解决方案**：
```python
# 使用 version 字段而不是 iteration_id
data = {
    'workspace_id': '35238004',
    'name': '需求名称',
    'version': '2026-0305',  # ✓ 正确：使用 version 字段
    # 'iteration_id': '20260305',  # ✗ 错误：需要实际的迭代 ID
}
```

### 4. 需求描述格式问题

**问题**：需求描述在 TAPD 上显示时没有换行，所有内容挤在一起

**原因**：TAPD 描述字段使用 HTML 格式，纯文本的 `\n` 不会被渲染为换行

**解决方案**：使用 HTML 标签
```python
description = '''<p><b>需求背景：</b></p>
<p>这是需求背景的内容。</p>
<br/>
<p><b>需求正文：</b></p>
<p>（1）第一条内容；</p>
<p>（2）第二条内容；</p>'''
```

### 5. API 限流问题

**问题**：连续调用 API 时返回 `429 Too Many Requests` 错误

**解决方案**：在 API 调用之间添加延迟
```bash
sleep 3 && export TAPD_TOKEN=... && python scripts/...
```

### 6. 创建需求脚本不存在

**问题**：`create_story.py` 脚本不存在

**解决方案**：该脚本已创建在 `scripts/workflow/create_story.py`，支持以下参数：
```bash
python scripts/workflow/create_story.py \
  --name "需求标题" \
  --description "需求描述（支持HTML）" \
  --owner "负责人" \
  --priority "3" \
  --iteration "迭代ID（可选）"
```

**注意**：
- 描述内容需要使用 HTML 格式才能正确显示换行
- 优先级：1-4，其中 4 为 High
- 可以先创建需求，再通过 POST 更新 `version` 字段

## 相关 Skills

- `/commit-cn` - 使用中文提交信息提交代码
- `/merge-to-test` - 合并到 test 分支
- `/release-doc-generator` - 生成发版文档
