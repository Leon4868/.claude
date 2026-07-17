# trigger-pipeline

使用 GitLab API 触发 CI/CD pipeline 构建和部署，支持自动检测变更模块并智能选择构建范围

**适用场景**: 当用户要求触发 pipeline、启动构建、部署到环境时使用

**触发短语**: "触发pipeline"、"启动构建"、"trigger pipeline"、"运行CI"、"部署"、"构建"、"build"、"打包"、"发布"

---

## 核心优化：智能模块检测

**新特性**：自动分析代码变更，只构建受影响的模块，避免全量构建浪费时间。

### 工作原理

1. **检测变更文件**：对比当前分支与 base 分支（如 master 或最新 release）
2. **识别受影响模块**：根据文件路径判断属于哪个模块
3. **智能决策**：
   - 只改了 1 个模块 → 自动构建该模块
   - 改了多个模块 → 询问用户选择构建哪些
   - 改了 common/api → 提示可能需要构建多个模块

### 模块映射规则

```
文件路径前缀 → 模块名称
├── callin/          → callin
├── hangup/          → hangup
├── scheduler/       → scheduler
├── server/          → server
├── number/          → number
├── xshield/         → xshield
├── xshadow/         → xshadow
├── state/           → state
├── common/          → common（影响所有模块）
├── api/             → api（影响所有模块）
└── 其他             → all（默认全量构建）
```

---

## 工作流程

### 1. 获取 GitLab Token

**优先级顺序**：
1. **首先尝试从环境变量读取**
2. **如果环境变量不存在**，询问用户提供 token
3. **如果用户提供了新 token**，询问是否保存到环境变量

**检查环境变量（Windows）**：

```bash
# 推荐：从系统注册表读取（最可靠）
powershell -Command "[System.Environment]::GetEnvironmentVariable('GITLAB_TOKEN', 'User')"
```

**保存到环境变量（Windows）**：
```powershell
# 永久保存，重启终端后生效
[System.Environment]::SetEnvironmentVariable('GITLAB_TOKEN', 'your-token-here', 'User')
```

### 2. 检测变更模块

**步骤 1：确定对比基准**

```bash
# 获取最新远程分支
git fetch origin

# 场景 1：对比 master 分支
BASE_SHA=$(git merge-base HEAD origin/master)

# 场景 2：对比最新 release 分支
LATEST_RELEASE=$(git branch -r | grep "origin/release_20" | grep -E "release_[0-9]{8}$" | sort | tail -1)
BASE_SHA=$(git merge-base HEAD $LATEST_RELEASE)
```

**步骤 2：获取变更文件列表**

```bash
# 获取变更的文件路径
git diff --name-only $BASE_SHA..HEAD
```

**步骤 3：分析受影响模块**

```bash
# 示例输出
callin/src/main/java/com/ai94/calltask/callin/service/CallInService.java
hangup/src/main/java/com/ai94/calltask/hangup/helper/HangupHelper.java
common/src/main/java/com/ai94/calltask/common/dal/dao/LlmPromptSolutionConfigDao.java
```

**分析结果**：
- 受影响模块：`callin`, `hangup`, `common`
- 建议：由于修改了 `common`，可能需要构建多个依赖它的模块

### 3. 智能决策构建范围

**场景 A：只修改了单个业务模块**

```
变更文件：
- hangup/src/main/java/.../HangupHelper.java
- hangup/src/main/resources/mapper/HangupMapper.xml

决策：自动构建 hangup 模块
```

**场景 B：修改了多个业务模块**

```
变更文件：
- callin/src/.../CallInService.java
- hangup/src/.../HangupHelper.java

决策：询问用户
选项：
1. 只构建 callin
2. 只构建 hangup
3. 构建 callin 和 hangup
4. 构建全部模块
```

**场景 C：修改了 common 或 api**

```
变更文件：
- common/src/.../LlmPromptSolutionConfigDao.java
- scheduler/src/.../LlmPromptSolutionConfigCache.java

决策：询问用户
提示：common 模块被多个模块依赖，建议：
1. 只构建 scheduler（如果确定只影响 scheduler）
2. 构建全部模块（推荐，确保兼容性）
```

**场景 D：修改了配置文件或文档**

```
变更文件：
- README.md
- .gitlab-ci.yml
- docs/guides/xxx.md

决策：询问用户是否需要构建
```

### 4. 触发 Pipeline

**基础触发（不指定模块，构建全部）**：

```bash
curl -X POST \
  --header "PRIVATE-TOKEN: <gitlab-token>" \
  --header "Content-Type: application/json" \
  --data '{"ref": "<branch-name>"}' \
  "http://gitlab.94ai.pro/api/v4/projects/atomic%2Fcall-task/pipeline"
```

**指定模块触发（推荐）**：

```bash
curl -X POST \
  --header "PRIVATE-TOKEN: <gitlab-token>" \
  --header "Content-Type: application/json" \
  --data '{
    "ref": "<branch-name>",
    "variables": [
      {"key": "SUB_MODULE", "value": "hangup"}
    ]
  }' \
  "http://gitlab.94ai.pro/api/v4/projects/atomic%2Fcall-task/pipeline"
```

**SUB_MODULE 可选值**（根据项目 .gitlab-ci.yml）：
- `all`: 构建所有模块（默认）
- `callin`: 呼入模块
- `hangup`: 挂断模块
- `scheduler`: 调度模块
- `server`: 服务模块
- `number`: 号码模块
- `xshield`: xshield 模块
- `xshadow`: xshadow 模块
- `state`: 状态模块

### 5. 输出结果

向用户报告：
- ✅ Pipeline 是否成功触发
- 📦 构建的模块范围
- 📊 Pipeline ID 和 IID
- 🔗 Pipeline 查看链接
- ⏱️ 预计节省的时间（如果是单模块构建）

**输出示例**：
```
成功触发！Pipeline 已经创建。

**触发结果**：
- ✅ Pipeline ID: `138062`
- 📦 构建模块: `hangup`（单模块构建）
- 🔗 查看地址: http://gitlab.94ai.pro/atomic/call-task/-/pipelines/138062
- 📍 分支: `test`
- 🔄 状态: `created`
- ⏱️ 预计节省: ~15 分钟（相比全量构建）

💡 提示：只构建了 hangup 模块，如果需要构建其他模块，请重新触发。
```

---

## 使用示例

### 示例 1：自动检测单模块变更

**用户**: "触发构建"

**助手行为**:
1. 检测变更：`git diff --name-only origin/master..HEAD`
2. 发现只修改了 `hangup/` 目录下的文件
3. 自动决策：构建 `hangup` 模块
4. 触发 pipeline，带参数 `SUB_MODULE=hangup`
5. 报告结果，说明节省了时间

### 示例 2：多模块变更，询问用户

**用户**: "构建一下"

**助手行为**:
1. 检测变更：修改了 `callin/` 和 `hangup/`
2. 询问用户：
   ```
   检测到变更涉及多个模块：
   - callin
   - hangup

   请选择构建范围：
   1. 只构建 callin
   2. 只构建 hangup
   3. 构建 callin 和 hangup
   4. 构建全部模块
   ```
3. 根据用户选择触发 pipeline

### 示例 3：修改了 common，提示风险

**用户**: "部署到测试环境"

**助手行为**:
1. 检测变更：修改了 `common/` 和 `scheduler/`
2. 提示用户：
   ```
   ⚠️ 检测到 common 模块变更，可能影响多个模块。

   变更模块：
   - common（被多个模块依赖）
   - scheduler

   建议：
   1. 只构建 scheduler（如果确定只影响 scheduler）
   2. 构建全部模块（推荐，确保兼容性）
   ```
3. 根据用户选择触发 pipeline

### 示例 4：用户明确指定模块

**用户**: "只构建 server 模块"

**助手行为**:
1. 跳过自动检测
2. 直接触发 pipeline，带参数 `SUB_MODULE=server`
3. 报告结果

---

## 高级功能

### 批量构建多个模块

如果用户选择构建多个模块（但不是全部），可以：

**方案 A：逐个触发**（推荐）
```bash
# 触发 callin
curl -X POST ... --data '{"ref": "test", "variables": [{"key": "SUB_MODULE", "value": "callin"}]}'

# 触发 hangup
curl -X POST ... --data '{"ref": "test", "variables": [{"key": "SUB_MODULE", "value": "hangup"}]}'
```

**方案 B：修改 .gitlab-ci.yml 支持多模块**（需要项目配置支持）
```bash
# 如果 CI 配置支持逗号分隔
curl -X POST ... --data '{"ref": "test", "variables": [{"key": "SUB_MODULE", "value": "callin,hangup"}]}'
```

### 查看模块依赖关系

在决策构建范围时，可以参考模块依赖：

```
依赖关系：
common → 被所有模块依赖
api → 被所有模块依赖
callin → 依赖 common, api
hangup → 依赖 common, api
scheduler → 依赖 common, api
server → 依赖 common, api
```

**规则**：
- 修改 `common` 或 `api` → 建议全量构建
- 修改业务模块 → 只构建该模块

---

## 注意事项

### 智能检测的局限性

1. **无法检测运行时依赖**：只能根据文件路径判断，无法分析代码中的调用关系
2. **配置文件变更**：修改 `.gitlab-ci.yml`、`pom.xml` 等可能影响所有模块
3. **数据库变更**：SQL 脚本变更可能影响多个模块

**建议**：
- 如果不确定，选择全量构建
- 单模块构建后，在测试环境验证功能
- 如果发现问题，重新全量构建

### 安全规范

- ❌ **禁止**在日志中暴露完整 token
- ❌ **禁止**将 token 提交到代码仓库
- ✅ **建议**使用环境变量存储 token
- ✅ **建议**定期轮换 token

---

## 错误处理

### 场景 1：无法检测变更

```
原因：当前分支没有对比基准（如新分支）

解决方案：
1. 询问用户要构建哪些模块
2. 或默认全量构建
```

### 场景 2：SUB_MODULE 值无效

```
错误：Pipeline 创建失败，提示 SUB_MODULE 值无效

解决方案：
1. 检查 .gitlab-ci.yml 中的 SUB_MODULE 选项
2. 确认模块名称拼写正确
3. 如果模块不存在，使用 all
```

---

## 相关技能

- `commit-cn`: 提交代码后可能需要触发 pipeline
- `merge-to-test`: 合并到 test 分支后可能需要触发 pipeline
- `commit-and-deploy`: 提交、合并、构建的完整流程

---

## 配置要求

### GitLab Token

需要有以下权限：
- `api`: 调用 GitLab API
- `read_repository`: 读取仓库信息

### 项目 CI 配置

`.gitlab-ci.yml` 需要支持 `SUB_MODULE` 变量：

```yaml
variables:
  SUB_MODULE:
    value: "all"
    options:
      - "all"
      - "callin"
      - "hangup"
      - "scheduler"
      - "server"
      - "number"
      - "xshield"
      - "xshadow"
      - "state"
    description: "选择要构建的模块"
```

---

## 总结

**优化前**：
- 每次都全量构建所有模块
- 耗时 ~30 分钟
- 浪费 CI 资源

**优化后**：
- 自动检测变更模块
- 只构建受影响的模块
- 单模块构建 ~5-10 分钟
- 节省 ~20 分钟和 CI 资源

**适用场景**：
- ✅ 单模块功能开发
- ✅ Bug 修复（通常只涉及一个模块）
- ✅ 快速验证（只需要测试某个模块）
- ❌ 大规模重构（建议全量构建）
- ❌ 发版前验证（建议全量构建）
