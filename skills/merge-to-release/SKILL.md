---
name: merge-to-release
description: 合并开发分支到 release 上线分支。从需求文档读取服务和分支信息，校验分支干净度（拒绝 test 污染），按发版顺序合并，支持 dry-run 模式。
---

# merge-to-release

合并开发分支到 release 上线分支，用于生产环境发版。

**适用场景**: 当用户要求将开发分支合并到 release 分支、准备上线发版时使用

**触发短语**: "合并到release"、"发版合并"、"merge to release"、"准备上线"、"创建release分支"

---

## 工作流程

当用户请求合并开发分支到 release 分支时，按以下 9 步执行：

### 1. 收集信息

从当前工作目录（tapd-requirements）的需求目录中读取发版所需信息。

**步骤 1：确定需求目录**

用户会指定需求目录，或从上下文推断。需求目录结构：
```
tapd-requirements/
└── <需求目录>/
    ├── development.md    # 开发文档（含涉及服务和开发分支）
    └── release.md        # 发版文档（含发版顺序和配置变更）
```

**步骤 2：读取 development.md**

从 `development.md` 中提取：
- **涉及服务列表**：每个服务的名称
- **开发分支名称**：每个服务对应的开发分支

**步骤 3：读取 release.md**

从 `release.md` 中提取：
- **发版顺序**：服务的部署先后顺序
- **配置变更**：SQL、Nacos、MQ 等配置信息

如果没有 `release.md`，使用 `development.md` 中的信息，发版顺序按依赖关系推断（基础库 → 中间层 → 上层应用）。

### 2. 定位服务目录

对每个涉及的服务，定位其本地 Git 仓库目录。

**默认路径规则**：`D:/Code/{服务名}`

```bash
# 验证目录存在且为 git 仓库
cd D:/Code/<服务名>
git rev-parse --is-inside-work-tree

# 拉取最新远程分支信息
git fetch origin
```

如果目录不存在，使用 AskUserQuestion 询问用户提供正确路径。

### 3. 确定 release 分支

**查找已有 release 分支**：

```bash
# 查找今天日期的 release 分支
git branch -r | grep "origin/release_$(date +%Y%m%d)"
```

**如果不存在，基于最新的 release 分支创建**：

```bash
# 查找最新的远程 release 分支（按日期排序取最新）
git branch -r | grep "origin/release_" | sort -t_ -k2 -rn | head -1

# 基于最新的 release 分支创建，不跟踪远程
git checkout -b release_<YYYYMMDD> origin/release_<最新日期> --no-track
```

> ⚠️ **禁止基于 master 创建 release 分支。** 必须基于最新的 release 分支创建，以确保包含之前发版的所有变更。
> 如果没有找到任何远程 release 分支，使用 AskUserQuestion 询问用户应基于哪个分支创建。

**如果已存在，直接 checkout**：

```bash
git checkout release_<YYYYMMDD>
git pull origin release_<YYYYMMDD>
```

**分支命名规则**：`release_YYYYMMDD`，如 `release_20260319`

### 4. 分支干净度校验（关键！）

> ⚠️ **必须在合并前校验 release 分支是否被 test 分支污染。发现污染立即停止，拒绝继续。**

```bash
# 确定基准分支（创建 release 分支时的基点）
# 如果是从远程拉取的：用 origin/master 或上一个 release 分支作为基准
# 只检查 release 分支分叉后的新增提交，避免历史记录误报
git log --oneline --merges <基准分支>..release_<YYYYMMDD> | grep -iE "Merge (branch 'test'|remote-tracking branch '.*/?test'|branch 'test' of)"
```

> ⚠️ **必须使用 `<基准分支>..release_<YYYYMMDD>` 范围查询**，只检查 release 分支自身新增的合并记录，不检查从基准分支继承的历史。
> 基准分支优先使用 `origin/master`，如果 release 是基于其他 release 分支创建的，则使用对应的父 release 分支。

**校验逻辑**：
- 如果 grep 有匹配结果 → **分支已被 test 污染，立即停止**
- 如果 grep 无匹配结果 → 分支干净，继续下一步

**污染时的处理**：
```
❌ release 分支 release_<YYYYMMDD> 已被 test 分支污染！

检测到以下 test 合并记录：
- <列出匹配的合并记录>

该分支不能用于生产发版。请执行以下操作之一：
1. 删除该 release 分支，重新从 master 创建
2. 使用其他干净的 release 分支

操作已终止，不会执行任何合并。
```

### 5. 合并开发分支

按 `release.md` 中的**发版顺序**依次合并每个服务的开发分支。

**对每个服务执行**：

```bash
cd D:/Code/<服务名>

# 确保在 release 分支上
git checkout release_<YYYYMMDD>

# 合并开发分支（必须 --no-ff）
git merge origin/<开发分支名> --no-ff -m "Merge branch '<开发分支名>' into release_<YYYYMMDD>"
```

**冲突处理（严格规则）**：

> ⚠️ **绝对禁止自行解决任何合并冲突。**

如果合并出现冲突：
1. 立即执行 `git merge --abort` 中止当前合并
2. **保留该服务之前已成功的合并**（不回滚整个 release 分支）
3. 报告冲突信息并停止该服务的后续合并
4. 继续处理下一个服务（如果有）

```
⚠️ 服务 <服务名> 合并 <开发分支名> 时出现冲突，已中止该次合并。

冲突文件：
- <列出冲突文件>

该服务之前已成功合并的分支不受影响。
请手动解决冲突后重新执行合并。
```

### 6. 代码审核（推送前）

所有服务合并完成后，在推送前询问用户是否需要审核代码变更。

```json
{
  "questions": [{
    "question": "所有服务的开发分支已合并到 release 分支（本地），是否需要在推送前审核代码？",
    "header": "代码审核",
    "multiSelect": false,
    "options": [
      {"label": "审核代码", "description": "调用 requesting-code-review 技能，对每个服务的 release 分支变更进行代码审核"},
      {"label": "跳过审核", "description": "信任已有的代码审查结果，直接进入推送步骤"}
    ]
  }]
}
```

**如果用户选择"审核代码"**：
- 对每个有实际新合并提交的服务，使用 Skill 工具调用 `requesting-code-review` 技能
- 审核范围：`origin/release_<上一个日期>..release_<YYYYMMDD>` 之间的变更
- 审核完成后，再进入推送步骤

**如果用户选择"跳过审核"**：
- 直接进入推送步骤

### 7. 推送远程

所有服务合并完成后，使用 AskUserQuestion 确认是否推送。

```json
{
  "questions": [{
    "question": "以下服务的 release 分支已准备好，是否推送到远程？",
    "header": "推送确认",
    "multiSelect": false,
    "options": [
      {"label": "全部推送", "description": "推送所有服务的 release 分支到远程"},
      {"label": "逐个确认", "description": "逐个服务确认是否推送"},
      {"label": "暂不推送", "description": "保留在本地，稍后手动推送"}
    ]
  }]
}
```

**推送命令**：
```bash
cd D:/Code/<服务名>
git push origin release_<YYYYMMDD>
```

### 8. 后续操作（可选）

推送完成后，使用 AskUserQuestion 询问用户是否需要执行后续操作：

```json
{
  "questions": [{
    "question": "release 分支已推送完成，是否需要执行后续操作？",
    "header": "后续操作",
    "multiSelect": true,
    "options": [
      {"label": "生成发版文档", "description": "调用 release-doc-generator 技能生成标准化发版文档"},
      {"label": "触发构建", "description": "调用 trigger-pipeline 技能触发 CI/CD pipeline 构建"},
      {"label": "不需要", "description": "合并流程到此结束"}
    ]
  }]
}
```

- 如果用户选择"生成发版文档"，使用 Skill 工具调用 `release-doc-generator` 技能
- 如果用户选择"触发构建"，使用 Skill 工具调用 `trigger-pipeline` 技能
- 两者可同时选择（multiSelect）

### 9. dry-run 模式

当用户指定 `--dry-run` 或 "只校验不合并" 时，执行步骤 1-4 但**跳过步骤 5-8**。

**dry-run 输出**：
```
🔍 Dry-run 校验结果：

服务：<服务名>
  ✅ 服务目录：D:/Code/<服务名>
  ✅ release 分支：release_<YYYYMMDD>（已存在/需新建）
  ✅ 分支干净度：无 test 污染
  📋 待合并分支：<开发分支名>

所有校验通过，可以执行实际合并。
去掉 --dry-run 参数重新执行即可。
```

---

## 安全规范

- ❌ **禁止** force push（`--force`、`-f`）
- ❌ **禁止**自动解决合并冲突（无论冲突多简单，一律中止）
- ❌ **禁止**合并被 test 分支污染的 release 分支
- ❌ **禁止**不使用 `--no-ff` 的合并（必须保留合并提交）
- ✅ **必须**在合并前校验分支干净度
- ✅ **必须**使用 `--no-ff` 保留分支历史
- ✅ **必须**在推送前通过 AskUserQuestion 询问是否需要代码审核
- ✅ **必须**在推送前通过 AskUserQuestion 获得用户确认
- ✅ **必须**按发版顺序合并（不可乱序）

---

## 错误处理

### 场景 1：需求文档不存在
```
❌ 未找到需求目录或 development.md 文件。
请确认需求目录路径，或手动提供以下信息：
- 涉及的服务列表
- 每个服务的开发分支名称
```

### 场景 2：服务目录不存在
```
❌ 未找到服务 <服务名> 的目录：D:/Code/<服务名>
请提供该服务的正确路径。
```

### 场景 3：release 分支被 test 污染
```
❌ release 分支已被 test 污染，操作终止。
请删除该分支并从 master 重新创建。
```

### 场景 4：合并冲突
```
⚠️ 合并冲突，已中止当前合并。
之前已成功的合并不受影响。
请手动解决冲突后重新执行。
```

### 场景 5：推送失败
```
❌ 推送失败，可能原因：
- 远程已有更新
- 网络问题
- 权限不足

建议：git pull origin release_<YYYYMMDD> 后重试
```

---

## 最终输出格式（重要！）

完成所有操作后，**必须输出清晰的汇总表格**，让用户一目了然地看到最终结果。

### 合并结果汇总

```
## ✅ 发版流程完成

### 合并结果

| 服务 | 分支 | 状态 |
|------|------|------|
| data-center | release_20260326 | ✅ 已推送 |
| ai-quartz | release_20260326 | ✅ 已推送 |
| task-aggre | release_20260326 | ✅ 已推送 |
| file-manager-center | release_20260326 | ✅ 已推送 |
```

### Pipeline 触发汇总

```
### Pipeline 触发结果

| 服务 | grayscale | prod |
|------|-----------|------|
| data-center | ✅ [#143986](链接) | ✅ [#143988](链接) |
| ai-quartz | ✅ [#144014](链接) | ✅ [#144016](链接) |
| task-aggre | ✅ [#143992](链接) | ✅ [#143993](链接) |
| file-manager-center | ✅ [#144015](链接) | ✅ [#144017](链接) |
```

### Pipeline 检查结果（验证 deploy 步骤）

**必须验证每个 Pipeline 是否包含 deploy 步骤**，确保构建流程完整：

```bash
# 检查 Pipeline 的 jobs
curl -s --header "PRIVATE-TOKEN: <token>" \
  "http://gitlab.94ai.pro/api/v4/projects/<project>/pipelines/<pipeline-id>/jobs" \
  | grep -o '"name":"[^"]*"' | grep -v "连武坤\|gitlab-runner"
```

**输出格式**：

```
## ✅ Pipeline 检查结果

| 服务 | 环境 | Pipeline | override tag | build | docker | deploy |
|------|------|----------|--------------|-------|--------|--------|
| **data-center** | grayscale | #143986 | - | ✅ | ✅ | ✅ trigger all deploy |
| **data-center** | prod | #143988 | ✅ | ✅ | ✅ | ✅ trigger all deploy |
| **ai-quartz** | grayscale | #144014 | - | ✅ | ✅ | ✅ trigger deploy quartz |
| **ai-quartz** | prod | #144016 | ✅ | ✅ | ✅ | ✅ trigger deploy quartz |
| **task-aggre** | grayscale | #143992 | - | ✅ | ✅ | ✅ trigger deploy |
| **task-aggre** | prod | #143993 | ✅ | ✅ | ✅ | ✅ trigger deploy |
| **file-manager-center** | grayscale | #144015 | - | ✅ | ✅ | ✅ trigger all deploy |
| **file-manager-center** | prod | #144017 | ✅ | ✅ | ✅ | ✅ trigger all deploy |

**所有 8 个 Pipeline 都包含 deploy 步骤！** ✅

- **grayscale 环境**: build → docker → deploy
- **prod 环境**: override image tag（生成生产镜像标签）→ build → docker → deploy
```

### 输出要点

1. **使用表格**：清晰展示多服务、多环境的状态
2. **使用图标**：✅ 成功、❌ 失败、⚠️ 警告
3. **提供链接**：Pipeline 编号必须是可点击的链接
4. **验证完整性**：必须检查 deploy 步骤存在，否则构建无效
5. **说明构建流程**：让用户理解 grayscale 和 prod 的区别

---

## 示例对话

**用户**: "把这三个需求合并到 release，需求目录在 tapd-requirements 下面"

**助手行为**:
1. 读取各需求目录的 `development.md` 和 `release.md`
2. 汇总所有涉及的服务和开发分支
3. 对每个服务：定位目录 → fetch → 创建/checkout release 分支 → 校验干净度 → 合并
4. 确认推送
5. 询问是否生成发版文档和触发构建

**用户**: "dry-run 检查一下 release 分支是否干净"

**助手行为**:
1. 读取需求文档
2. 定位服务目录
3. 检查 release 分支是否存在
4. 校验分支干净度
5. 输出校验结果，不执行合并

---

## 相关技能

- `merge-to-test`: 合并到 test 分支（测试环境）
- `release-doc-generator`: 生成发版文档
- `trigger-pipeline`: 触发 CI/CD pipeline
- `commit-cn`: 提交代码
- `tapd`: 需求管理
