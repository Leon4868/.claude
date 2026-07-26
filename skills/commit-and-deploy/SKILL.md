---
name: commit-and-deploy
description: 交互式提交代码并可选合并到test分支和触发构建
---

# commit-and-deploy

交互式提交代码工作流，支持提交、合并到test分支、触发构建的组合操作。

**适用场景**: 当用户要求提交代码、发布代码、部署代码时使用

**触发短语**: "提交代码"、"提交并部署"、"commit"、"发布"

---

## 工作流程

### 1. 检查当前状态

并行运行以下命令了解当前状态：

```bash
# 查看当前分支
git branch --show-current

# 查看 git 状态
git status

# 查看未暂存的修改
git diff --stat
```

**验证点**：
- 确认当前分支名称
- 确认是否有未提交的修改
- 如果没有修改，询问用户是否继续（见下方"工作区干净时的处理"）

#### 工作区干净时的处理

**场景**：当前分支没有未提交的修改（工作区干净）

**处理方式**：使用 AskUserQuestion 工具询问用户是否进行代码审查：

```json
{
  "questions": [
    {
      "question": "将执行合并到 test 分支并触发构建。是否先进行代码审查？",
      "header": "代码审查",
      "multiSelect": false,
      "options": [
        {
          "label": "进行代码审查（推荐）",
          "description": "自动检查代码质量、安全性、性能等，确保代码质量"
        },
        {
          "label": "跳过代码审查",
          "description": "直接合并并构建，适合紧急修复或小改动"
        },
        {
          "label": "取消操作",
          "description": "结束流程，不进行任何操作"
        }
      ]
    }
  ]
}
```

**执行流程**：
- **进行代码审查**：
  1. 调用 `requesting-code-review` 技能
  2. 执行合并到 test 分支（调用 `merge-to-test` 技能）
  3. 触发 pipeline 构建（调用 `trigger-pipeline` 技能）
- **跳过代码审查**：
  1. 执行合并到 test 分支（调用 `merge-to-test` 技能）
  2. 触发 pipeline 构建（调用 `trigger-pipeline` 技能）
- **取消操作**：
  - 显示提示信息并结束流程

### 2. 显示交互式选项（有修改时）

**场景**：当前分支有未提交的修改

**处理方式**：使用 AskUserQuestion 工具询问用户是否进行代码审查：

```json
{
  "questions": [
    {
      "question": "将执行提交、合并到 test 分支并触发构建。是否先进行代码审查？",
      "header": "代码审查",
      "multiSelect": false,
      "options": [
        {
          "label": "进行代码审查（推荐）",
          "description": "自动检查代码质量、安全性、性能等，确保代码质量"
        },
        {
          "label": "跳过代码审查",
          "description": "直接提交、合并并构建，适合紧急修复或小改动"
        },
        {
          "label": "仅提交代码",
          "description": "只提交到当前分支，不合并不构建"
        }
      ]
    }
  ]
}
```

**选项说明**：
- **进行代码审查**：调用 `requesting-code-review` 技能，检查代码质量、安全性、性能、可维护性，然后执行提交→合并→构建
- **跳过代码审查**：直接执行提交→合并→构建，节省时间
- **仅提交代码**：只提交到当前分支，不进行后续的合并和构建操作

**推荐场景**：
- ✅ **推荐审查**：新功能、重构、涉及核心逻辑、多文件修改
- ⚠️ **可跳过审查**：紧急修复、配置修改、文档更新、单行小改动

### 3. 执行用户选择的操作

**重要**: 本技能作为编排器，通过调用其他专门技能来完成任务，而不是重复实现逻辑。

根据用户选择执行相应操作：

#### 选项 1: 进行代码审查（推荐）

**执行流程**：

1. **提交代码**：调用 `commit-cn` 技能提交代码到当前分支

2. **代码审查**：调用 `requesting-code-review` 技能进行代码审查
   - 等待审查结果，如果发现严重问题，流程中断
   - 如果审查通过或只有轻微问题，继续下一步

3. **合并到test**：merge-to-test 技能必须在内部先切换到 test 分支，再更新 test 并合并 feature 分支；禁止在 feature 分支上直接执行 git pull origin test。
   - **如果当前在 feature 分支**：调用 merge-to-test 技能合并到 test 分支
   - **如果当前已在 test 分支**：跳过合并步骤（已经在目标分支）

4. **触发构建**：调用 `trigger-pipeline` 技能触发 test 分支的构建

**调用示例**：
```
Skill(skill="commit-cn")
Skill(skill="requesting-code-review")
# 等待审查结果，如果通过则继续
# 检查当前分支，如果不是 test 分支则合并
if current_branch != "test":
    Skill(skill="merge-to-test")
# 触发 test 分支的 pipeline
Skill(skill="trigger-pipeline", args="test")
```

---

#### 选项 2: 跳过代码审查

**执行流程**：

1. **提交代码**：调用 `commit-cn` 技能提交代码到当前分支

2. **合并到test**：
   - **如果当前在 feature 分支**：调用 `merge-to-test` 技能合并到 test 分支
   - **如果当前已在 test 分支**：跳过合并步骤（已经在目标分支）

3. **触发构建**：调用 `trigger-pipeline` 技能触发 test 分支的构建

**调用示例**：
```
Skill(skill="commit-cn")
# 检查当前分支，如果不是 test 分支则合并
if current_branch != "test":
    Skill(skill="merge-to-test")
# 触发 test 分支的 pipeline
Skill(skill="trigger-pipeline", args="test")
```

---

#### 选项 3: 仅提交代码

**调用技能**: `commit-cn`

使用 Skill 工具调用 commit-cn 技能：
```
Skill(skill="commit-cn")
```

commit-cn 技能会自动：
1. 查看修改内容（git diff）
2. 添加文件到暂存区（git add）
3. 生成符合规范的中文提交信息
4. 提交代码（git commit）
5. 推送到远程当前分支（git push）

**适用场景**：开发过程中的临时保存，不需要审查和合并

---

#### 工作区干净时的执行流程

**进行代码审查**：
```
Skill(skill="requesting-code-review")
# 等待审查结果，如果通过则继续
if current_branch != "test":
    Skill(skill="merge-to-test")
Skill(skill="trigger-pipeline", args="test")
```

**跳过代码审查**：
```
if current_branch != "test":
    Skill(skill="merge-to-test")
Skill(skill="trigger-pipeline", args="test")
```

**取消操作**：
- 显示提示信息并结束流程

---

## 技能编排说明

本技能作为**编排器（Orchestrator）**，不重复实现具体逻辑，而是通过调用专门的技能来完成任务：

- **commit-cn**: 负责提交代码的所有逻辑（分析修改、生成提交信息、git 操作）
- **requesting-code-review**: 负责代码审查的所有逻辑（分析代码质量、安全性、性能、可维护性、对比最新 release 分支）
- **merge-to-test**: 负责合并到 test 分支的所有逻辑（切换分支、合并、推送）
- **trigger-pipeline**: 负责触发构建的所有逻辑（读取 token、调用 API、显示结果）

**工作流程（有修改时）**：

```
进行代码审查: commit-cn → requesting-code-review → merge-to-test → trigger-pipeline
跳过代码审查: commit-cn → merge-to-test → trigger-pipeline
仅提交代码: commit-cn
```

**工作流程（工作区干净时）**：

```
进行代码审查: requesting-code-review → merge-to-test → trigger-pipeline
跳过代码审查: merge-to-test → trigger-pipeline
取消操作: 结束流程
```

**代码审查门禁（可选）**：
- 用户可以选择是否进行代码审查
- 如果选择"进行代码审查"：
  - 调用 `requesting-code-review` 技能检查代码质量、安全性、性能、可维护性
  - 对比最新 release 分支，了解相对于生产环境的所有变更
  - 如果发现严重问题（如安全漏洞），流程会中断
  - 如果只有轻微问题（如命名建议），会显示警告但允许继续
- 如果选择"跳过代码审查"：
  - 直接执行合并和构建，节省时间
  - 适合紧急修复或小改动

**优势**：
1. **单一职责**: 每个技能专注做好一件事
2. **可复用**: 用户可以单独使用任何一个技能
3. **易维护**: 修改某个功能只需要修改对应的技能
4. **灵活组合**: 通过编排器提供不同的组合方式
5. **简化流程**: 默认执行完整流程，减少选择步骤

---

## 提交信息生成规则

**注意**: 提交信息由 `commit-cn` 技能自动生成，本技能不需要处理。

commit-cn 技能会根据修改内容自动生成符合规范的提交信息：

**格式**: `<type>(<scope>): <subject>`

**类型（type）**：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档修改
- `refactor`: 重构代码
- `test`: 测试相关
- `chore`: 构建/工具/配置修改

**作用域（scope）**：
- 根据修改的文件路径确定（如 xshield, hangup, server 等）

**描述（subject）**：
- 简洁描述修改内容
- 中文描述，不超过50字

---

## 示例对话

### 示例 1：有修改时进行代码审查

**用户**: "提交代码"

**助手行为**:
1. 检查 git 状态，发现有未提交的修改
2. 显示问题：是否先进行代码审查？
3. 用户选择"进行代码审查"
4. 依次调用技能：
   - 调用 `commit-cn` 技能提交代码
   - 调用 `requesting-code-review` 技能进行代码审查
   - 调用 `merge-to-test` 技能合并到 test 分支
   - 调用 `trigger-pipeline` 技能触发构建
5. 显示最终结果（合并状态、pipeline 链接）

### 示例 2：有修改时跳过代码审查

**用户**: "提交代码"

**助手行为**:
1. 检查 git 状态，发现有未提交的修改
2. 显示问题：是否先进行代码审查？
3. 用户选择"跳过代码审查"
4. 依次调用技能：
   - 调用 `commit-cn` 技能提交代码
   - 调用 `merge-to-test` 技能合并到 test 分支
   - 调用 `trigger-pipeline` 技能触发构建
5. 显示最终结果（合并状态、pipeline 链接）

### 示例 3：仅提交代码

**用户**: "提交代码"

**助手行为**:
1. 检查 git 状态，发现有未提交的修改
2. 显示问题：是否先进行代码审查？
3. 用户选择"仅提交代码"
4. 调用 `commit-cn` 技能提交代码
5. 显示提交结果

### 示例 4：工作区干净时合并并构建

**用户**: "提交代码"

**助手行为**:
1. 检查 git 状态，发现没有未提交的修改（工作区干净）
2. 显示问题：将执行合并到 test 分支并触发构建。是否先进行代码审查？
3. 用户选择"跳过代码审查"
4. 依次调用技能：
   - 调用 `merge-to-test` 技能合并到 test 分支
   - 调用 `trigger-pipeline` 技能触发构建
5. 显示最终结果（合并状态、pipeline 链接）

### 示例 5：工作区干净时取消操作

**用户**: "提交代码"

**助手行为**:
1. 检查 git 状态，发现没有未提交的修改（工作区干净）
2. 显示问题：将执行合并到 test 分支并触发构建。是否先进行代码审查？
3. 用户选择"取消操作"
4. 显示提示信息："已取消操作，当前工作区干净，没有需要提交的修改。"
5. 结束流程

---

## 注意事项

1. **技能调用顺序**：
   - 进行代码审查：`commit-cn` → `requesting-code-review` → `merge-to-test`（如果不在test分支） → `trigger-pipeline`
   - 跳过代码审查：`commit-cn` → `merge-to-test`（如果不在test分支） → `trigger-pipeline`
   - 仅提交代码：`commit-cn`
   - 每个技能必须等待前一个完成后再执行
   - 如果某个技能失败，停止后续流程并报告错误

2. **当前分支检查**：
   - **关键**：在执行合并和构建时，必须检查当前分支
   - 如果当前在 feature 分支：
     - commit-cn 会提交到 feature 分支
     - merge-to-test 会将 feature 分支合并到 test 分支
     - trigger-pipeline 会触发 test 分支的构建
   - 如果当前已在 test 分支：
     - commit-cn 会直接提交到 test 分支
     - 跳过 merge-to-test（已经在目标分支）
     - trigger-pipeline 会触发 test 分支的构建
   - **错误示例**：在 feature 分支提交后，直接触发 test 分支的 pipeline，但 test 分支还没有包含新提交

3. **代码审查门禁（可选）**：
   - 用户可以选择是否进行代码审查
   - 如果选择"进行代码审查"：
     - requesting-code-review 会检查：
       - 代码质量（复杂度、可读性、命名规范）
       - 安全性（SQL 注入、XSS、敏感信息泄露）
       - 性能（N+1 查询、大循环、资源泄露）
       - 可维护性（重复代码、过长方法、耦合度）
       - 对比最新 release 分支，了解相对于生产环境的所有变更
     - 如果发现严重问题（如安全漏洞），流程会中断
     - 如果只有轻微问题（如命名建议），会显示警告但允许继续
   - 如果选择"跳过代码审查"：
     - 直接执行合并和构建，节省时间
     - 适合紧急修复或小改动

4. **错误处理**：
   - 如果 commit-cn 失败（如没有修改、提交冲突），停止流程
   - 如果 requesting-code-review 发现严重问题，停止流程并显示审查报告
   - 如果 merge-to-test 失败（如合并冲突），提示用户手动解决
   - 如果 trigger-pipeline 失败（如 token 无效），显示错误信息

5. **工作区状态检查**：
   - 在显示选项前，检查当前是否有未提交的修改
   - **如果有修改**：显示代码审查选项（默认执行提交→合并→构建）
   - **如果没有修改**：显示代码审查选项（默认执行合并→构建）
   - 如果在 master/main 分支，提示用户切换到功能分支

6. **用户体验**：
   - 显示清晰的进度提示（正在提交、正在审查、正在合并、正在触发构建）
   - 每个步骤完成后显示结果
   - 如果进行代码审查，审查完成后显示审查报告摘要
   - 最后显示完整的操作摘要

---

## 常见问题和解决方案

### 问题 1：在 feature 分支提交后，触发的 pipeline 不包含新提交

**症状**：
- 用户在 feature 分支上提交了代码
- 触发了 test 分支的 pipeline
- 但 pipeline 构建的是旧代码，不包含新提交

**原因**：
- commit-cn 提交到了 feature 分支
- 但没有合并到 test 分支
- 直接触发 test 分支的 pipeline，test 分支还没有包含新提交

**解决方案**：
1. 检查当前分支：`git branch --show-current`
2. 如果不在 test 分支，必须先调用 `merge-to-test` 合并
3. 然后再调用 `trigger-pipeline` 触发构建

**正确流程**：
```
当前分支: feature
↓
commit-cn (提交到 feature 分支)
↓
requesting-code-review (审查 feature 分支的提交)
↓
merge-to-test (合并 feature → test)
↓
trigger-pipeline (触发 test 分支的 pipeline)
```

### 问题 2：commit-cn 执行顺序错误

**症状**：
- 先执行 `git push`，显示 "Everything up-to-date"
- 然后才执行 `git commit`
- 导致提交成功但没有推送

**原因**：
- 命令顺序错误：`git add && git push && git commit`
- 正确顺序应该是：`git add && git commit && git push`

**解决方案**：
- 已在 commit-cn 技能文档中明确说明正确顺序
- 使用单个命令链接：`git add ... && git commit ... && git push ...`

### 问题 3：代码审查发现问题后，如何处理

**症状**：
- requesting-code-review 发现 Important 级别的问题
- 用户不确定是否应该继续

**解决方案**：
1. 使用 AskUserQuestion 询问用户：
   - 修复后继续
   - 直接构建（跳过修复）
   - 停止流程
2. 如果用户选择"修复后继续"：
   - 修改代码
   - 重新提交
   - 重新审查
   - 继续后续流程

### 问题 4：如何决定是否进行代码审查

**推荐进行代码审查的场景**：
- 新功能开发
- 代码重构
- 涉及核心业务逻辑
- 多文件修改（3个以上）
- 涉及数据库操作
- 涉及安全相关代码

**可以跳过代码审查的场景**：
- 紧急修复（生产环境问题）
- 配置文件修改
- 文档更新
- 单行小改动
- 注释修改
- 格式化代码

---

## 相关技能

- `commit-cn`: 中文提交信息（被本技能调用）
- `requesting-code-review`: 代码审查（被本技能调用，用于选项 2 和 3）
- `merge-to-test`: 合并到test分支（被本技能调用）
- `trigger-pipeline`: 触发pipeline构建（被本技能调用）
- `receiving-code-review`: 接收代码审查反馈（当审查发现问题时使用）

---

## 技术实现

### 有修改时的交互式选项

使用 AskUserQuestion 工具创建交互式选项：

```json
{
  "questions": [
    {
      "question": "将执行提交、合并到 test 分支并触发构建。是否先进行代码审查？",
      "header": "代码审查",
      "multiSelect": false,
      "options": [
        {
          "label": "进行代码审查（推荐）",
          "description": "自动检查代码质量、安全性、性能等，确保代码质量"
        },
        {
          "label": "跳过代码审查",
          "description": "直接提交、合并并构建，适合紧急修复或小改动"
        },
        {
          "label": "仅提交代码",
          "description": "只提交到当前分支，不合并不构建"
        }
      ]
    }
  ]
}
```

### 工作区干净时的交互式选项

```json
{
  "questions": [
    {
      "question": "将执行合并到 test 分支并触发构建。是否先进行代码审查？",
      "header": "代码审查",
      "multiSelect": false,
      "options": [
        {
          "label": "进行代码审查（推荐）",
          "description": "自动检查代码质量、安全性、性能等，确保代码质量"
        },
        {
          "label": "跳过代码审查",
          "description": "直接合并并构建，适合紧急修复或小改动"
        },
        {
          "label": "取消操作",
          "description": "结束流程，不进行任何操作"
        }
      ]
    }
  ]
}
```




