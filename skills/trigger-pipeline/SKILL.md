---
name: trigger-pipeline
description: 使用 GitLab API 触发 CI/CD pipeline 构建和部署
---

# trigger-pipeline

使用 GitLab API 触发 CI/CD pipeline 构建和部署

**适用场景**: 当用户要求触发 pipeline、启动构建、部署到环境时使用

**触发短语**: "触发pipeline"、"启动构建"、"trigger pipeline"、"运行CI"、"部署"、"构建"、"build"、"打包"、"发布"

---

## 工作流程

当用户请求触发 pipeline 时，按以下步骤执行：

### 1. 获取 GitLab Token

**优先级顺序**：
1. **首先尝试从环境变量读取**
2. **如果环境变量不存在**，询问用户提供 token
3. **如果用户提供了新 token**，询问是否保存到环境变量

**检查环境变量（兼容 bash 和 PowerShell）**：

由于 Bash 工具可能运行在不同的 shell 环境中，需要使用兼容的方式检查：

```bash
# 方法 1：使用 PowerShell 从系统注册表读取（推荐，最可靠）
powershell -Command "[System.Environment]::GetEnvironmentVariable('GITLAB_TOKEN', 'User')"

# 方法 2：在 bash 中直接读取（如果当前会话已加载）
echo $GITLAB_TOKEN

# 方法 3：在 PowerShell 中读取（需要明确调用 PowerShell）
powershell -Command '$env:GITLAB_TOKEN'
```

**推荐使用方法 1**，因为它直接从系统注册表读取用户级别的环境变量，不受当前 shell 会话的影响。

**注意事项**：
- 在 Windows 上，用户级别的环境变量存储在注册表中
- 新启动的进程会自动继承这些环境变量
- 但已经运行的进程（如当前 bash 会话）不会自动更新
- 使用 `[System.Environment]::GetEnvironmentVariable()` 可以直接读取注册表，绕过会话限制

**保存到环境变量**：
```bash
# Windows (PowerShell) - 永久保存，重启终端后生效
[System.Environment]::SetEnvironmentVariable('GITLAB_TOKEN', 'your-token-here', 'User')

# Windows (CMD) - 永久保存，重启终端后生效
setx GITLAB_TOKEN "your-token-here"

# Windows (PowerShell) - 临时保存，仅当前会话有效
$env:GITLAB_TOKEN = "your-token-here"

# Linux/Mac (Bash) - 永久保存，添加到 ~/.bashrc 或 ~/.zshrc
echo 'export GITLAB_TOKEN="your-token-here"' >> ~/.bashrc
source ~/.bashrc

# Linux/Mac (Bash) - 临时保存，仅当前会话有效
export GITLAB_TOKEN="your-token-here"
```

### 2. 检查当前状态

并行运行以下命令了解当前状态：

```bash
# 查看当前分支
git branch --show-current

# 查看远程仓库信息
git remote -v

# 查看最近的提交
git log --oneline -3
```

**验证点**：
- 确认当前分支名称
- 确认 GitLab 项目地址
- 记录最新的提交 SHA

### 3. 智能识别构建模块（重要！）

**目的**：避免不必要的全量构建，只构建有变更的模块。

**步骤 1：读取 CI 配置**
```bash
# 读取 .gitlab-ci.yml 确认项目支持的模块
cat .gitlab-ci.yml | grep -A 10 "SUB_MODULE:"
```

**步骤 2：分析代码变更**

根据触发场景选择不同的分析策略：

**场景 A：合并到 test 后立即触发（推荐）**
```bash
# 查看最近一次合并提交涉及的文件
git diff --name-only HEAD~1 HEAD
```

**场景 B：用户指定分支触发**
```bash
# 查看该分支相对于 test 分支的变更
git diff --name-only origin/test...HEAD
```

**场景 C：用户明确指定模块**
- 直接使用用户指定的模块，跳过自动识别

**步骤 3：模块映射规则**

根据文件路径识别模块：
- `callin/` → `callin`
- `hangup/` → `hangup`
- `scheduler/` → `scheduler`
- `server/` → `server`
- `state/` → `state`
- `xshield/` → `xshield`
- `number/` → `number`
- `common/` → `all`（公共模块影响所有服务）
- `api/` → `all`（API 模块影响所有服务）
- `.gitlab-ci.yml` → `all`（CI 配置变更需要全量构建）
- `pom.xml`（根目录） → `all`（依赖变更需要全量构建）

**步骤 4：决策逻辑**

```
IF 用户明确指定模块:
    使用用户指定的模块
ELSE IF 变更涉及 common/api/根pom.xml/.gitlab-ci.yml:
    SUB_MODULE = "all"
ELSE IF 变更只涉及单个模块目录:
    SUB_MODULE = 该模块名
ELSE IF 变更涉及多个模块目录:
    询问用户选择：
    - 构建所有变更的模块（逗号分隔，如 "scheduler,hangup"）
    - 构建全部模块（"all"）
    - 只构建特定模块（让用户选择）
ELSE:
    SUB_MODULE = "all"（默认全量构建）
```

**示例输出**：
```
检测到代码变更：
- scheduler/src/main/java/.../LlmPromptSolutionConfigCache.java

识别到变更模块：scheduler

建议构建模块：scheduler（只构建变更的模块，节省时间）
```

### 4. 触发 Pipeline

**基础触发（不推荐，会构建所有模块）**：

```bash
curl -X POST \
  --header "PRIVATE-TOKEN: <gitlab-token>" \
  --header "Content-Type: application/json" \
  --data '{"ref": "<branch-name>"}' \
  "http://gitlab.94ai.pro/api/v4/projects/<project-path>/pipeline"
```

**智能触发（推荐，只构建变更的模块）**：

```bash
curl -X POST \
  --header "PRIVATE-TOKEN: <gitlab-token>" \
  --header "Content-Type: application/json" \
  --data '{
    "ref": "<branch-name>",
    "variables": [
      {"key": "SUB_MODULE", "value": "<module-name>"},
      {"key": "ENVIRONMENT_NAME", "value": "<environment>"}
    ]
  }' \
  "http://gitlab.94ai.pro/api/v4/projects/<project-path>/pipeline"
```

**参数说明**：
- `<gitlab-token>`: GitLab Personal Access Token
  - 需要有 `api` 权限
  - 可以从用户获取或使用项目配置的 token
  - 安全起见，建议使用环境变量或配置文件存储
- `<project-path>`: 项目路径，需要 URL 编码（从 `git remote -v` 提取，如 `atomic%2Fcall-task`）
- `<branch-name>`: 要触发的分支名称
- `<module-name>`: 从步骤 3 识别的模块名（如 `scheduler`、`hangup`、`all` 等）
- `<environment>`: 环境名称，根据分支名自动推断（见下方规则）

**ENVIRONMENT_NAME 自动推断规则（重要！）**：

根据触发的分支名自动设置 `ENVIRONMENT_NAME`：

| 分支名模式 | ENVIRONMENT_NAME | 说明 |
|-----------|-----------------|------|
| `release_*` | 使用 AskUserQuestion 询问 | release 分支需要用户选择部署环境（见下方） |
| `test` | `test` | 测试分支 |
| `develop*` | `dev` | 开发分支 |
| 其他 | `test` | 默认测试环境 |

**release 分支环境选择（必须询问用户）**：

当触发的分支名匹配 `release_*` 时，使用 AskUserQuestion 询问部署环境：

```json
{
  "questions": [{
    "question": "release 分支需要部署到哪些环境？",
    "header": "部署环境",
    "multiSelect": true,
    "options": [
      {"label": "prod", "description": "生产环境，会执行 override image tag 生成生产镜像标签"},
      {"label": "grayscale", "description": "灰度环境，用于灰度验证"}
    ]
  }]
}
```

如果用户选择了多个环境，需要为每个环境分别触发一次 pipeline（同一个分支、同一个 SUB_MODULE，不同的 ENVIRONMENT_NAME）。

> ⚠️ **release 分支选择 `prod` 时**，CI 中的 `override image tag` job 才会执行（该 job 的 rules 要求 `$ENVIRONMENT_NAME == "prod" && $CI_COMMIT_REF_NAME =~ /^release.*/`），生成格式为 `v_release_YYYYMMDD_HHMM` 的生产镜像标签。选择其他环境则不会执行该 job。

**自动识别项目路径**：
从 `git remote -v` 输出中提取项目路径：
- 示例：`http://gitlab.94ai.pro/atomic/call-task.git`
- 提取：`atomic/call-task`
- URL 编码：`atomic%2Fcall-task`（将 `/` 替换为 `%2F`）

**重要提示**：
- ✅ **必须**使用步骤 3 识别的模块名设置 `SUB_MODULE` 变量
- ✅ **必须**在输出中告知用户构建了哪些模块
- ❌ **禁止**在只修改单个模块时触发全量构建（`SUB_MODULE=all`）

### 5. 多服务依赖构建（重要！）

当需要触发多个有依赖关系的服务时（如从 merge-to-release 技能调用），**必须按依赖顺序逐个触发，等上游服务构建成功后再触发下游服务**。

**原因**：下游服务编译时依赖上游服务的 Maven 产物（如 constants jar 包），如果上游还没构建完成，下游会因找不到依赖而编译失败。

**执行流程**：

```
1. 按发版顺序排列服务（如 constants → ai → data-center）
2. 触发第一个服务的 pipeline
3. 轮询等待该 pipeline 完成：
   - 每 15 秒查询一次状态
   - 如果状态为 success → 继续触发下一个服务
   - 如果状态为 failed → 停止，报告错误，不触发后续服务
4. 重复步骤 3 直到所有服务构建完成
```

**轮询状态命令**：

```bash
# 查询 pipeline 状态
curl -s --header "PRIVATE-TOKEN: <gitlab-token>" \
  "http://gitlab.94ai.pro/api/v4/projects/<project-path>/pipelines/<pipeline-id>" \
  | python -c "import sys,json; print(json.load(sys.stdin)['status'])"
```

**状态判断**：
- `success` → 构建成功，触发下一个服务
- `failed` → 构建失败，停止后续触发，报告错误
- `canceled` → 已取消，停止后续触发
- `created`、`pending`、`running` → 仍在进行中，继续等待

**超时处理**：
- 单个 pipeline 最长等待 15 分钟
- 超时后使用 AskUserQuestion 询问用户：继续等待 / 跳过该服务继续下一个 / 终止

**示例输出**：
```
按依赖顺序触发构建：

[1/3] constants — Pipeline #142029 已触发，等待完成...
  ⏳ 状态: running (15s)
  ⏳ 状态: running (30s)
  ✅ 状态: success (45s)

[2/3] ai — Pipeline #142031 已触发，等待完成...
  ⏳ 状态: running (15s)
  ✅ 状态: success (30s)

[3/3] data-center — Pipeline #142035 已触发，等待完成...
  ⏳ 状态: running (15s)
  ✅ 状态: success (60s)

全部构建完成！
```

**单服务触发时**：无需等待，直接触发并返回结果即可。

### 6. 解析响应

API 返回的 JSON 包含：
- `id`: Pipeline ID
- `iid`: Pipeline IID（项目内的序号）
- `web_url`: Pipeline 查看地址
- `status`: 当前状态（created, pending, running, success, failed 等）
- `ref`: 触发的分支
- `sha`: 提交 SHA

### 7. 保存 Token（可选）

如果用户提供了新的 token，询问是否保存到环境变量以便后续使用。

**Windows 保存方法**：
```powershell
# 方法 1：PowerShell（推荐）- 永久保存，重启终端后生效
[System.Environment]::SetEnvironmentVariable('GITLAB_TOKEN', 'your-token-here', 'User')

# 方法 2：CMD - 永久保存，重启终端后生效
setx GITLAB_TOKEN "your-token-here"

# 方法 3：PowerShell - 临时保存，仅当前会话有效
$env:GITLAB_TOKEN = "your-token-here"
```

**Linux/Mac 保存方法**：
```bash
# 永久保存 - 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export GITLAB_TOKEN="your-token-here"' >> ~/.bashrc
source ~/.bashrc

# 临时保存 - 仅当前会话有效
export GITLAB_TOKEN="your-token-here"
```

**重要提示**：
- 使用 `setx` 或 `SetEnvironmentVariable` 保存后，需要**重启终端**才能生效
- 如果需要立即在当前会话使用，可以同时执行临时保存命令
- 保存后可以用 `echo $env:GITLAB_TOKEN`（Windows）或 `echo $GITLAB_TOKEN`（Linux/Mac）验证

### 8. 输出结果

向用户报告：
- ✅ Pipeline 是否成功触发
- 📊 Pipeline ID 和 IID
- 🔗 Pipeline 查看链接
- 📍 触发的分支和提交
- 🔄 当前状态
- 🎯 **构建模块**（重要！必须告知用户）

**输出示例**：
```
成功触发！Pipeline 已经创建。

**触发结果**：
- ✅ Pipeline ID: `138076`
- 📊 Pipeline IID: `4048`
- 🔗 查看地址: http://gitlab.94ai.pro/atomic/call-task/-/pipelines/138076
- 📍 分支: `test`
- 🔄 状态: `created`（已创建，等待执行）
- 👤 触发者: 连武坤 (lianwukun)
- 📝 提交: `5834f1a04`
- 🎯 构建模块: `scheduler`（只构建变更的模块，节省时间）

Pipeline 已经开始运行，你可以点击链接查看构建进度。
```

---

## 高级用法

### 带变量触发

如果需要指定构建变量（如模块、环境等）：

```bash
curl -X POST \
  --header "PRIVATE-TOKEN: <gitlab-token>" \
  --header "Content-Type: application/json" \
  --data '{
    "ref": "<branch-name>",
    "variables": [
      {"key": "SUB_MODULE", "value": "hangup"},
      {"key": "ENVIRONMENT_NAME", "value": "test"}
    ]
  }' \
  "http://gitlab.94ai.pro/api/v4/projects/<project-path>/pipeline"
```

**常用变量**（需要根据项目的 `.gitlab-ci.yml` 确认）：

**示例 1：单模块项目（如 tiktok-shop）**
- `SUB_MODULE`:
  - `all`: 构建所有模块（默认）
  - `tiktok-shop-server`: 服务模块
- `ENVIRONMENT_NAME`:
  - `test`: 测试环境（默认）
  - `dev`: 开发环境
  - `grayscale`: 灰度环境
  - `prod`: 生产环境

**示例 2：多模块项目（如 call-task）**
- `SUB_MODULE`:
  - `all`: 构建所有模块（默认）
  - `callin`: 呼入模块
  - `hangup`: 挂断模块
  - `scheduler`: 调度模块
  - `server`: 服务模块
  - 其他模块...
- `ENVIRONMENT_NAME`: 同上

**如何确定项目的变量选项**：
1. 查看项目根目录的 `.gitlab-ci.yml` 文件
2. 找到 `variables` 部分
3. 查看 `SUB_MODULE` 和 `ENVIRONMENT_NAME` 的 `options` 配置

### 查询 Pipeline 状态

触发后可以查询 pipeline 状态：

```bash
curl --header "PRIVATE-TOKEN: <gitlab-token>" \
  "http://gitlab.94ai.pro/api/v4/projects/<project-path>/pipelines/<pipeline-id>"
```

### 取消 Pipeline

如果需要取消正在运行的 pipeline：

```bash
curl -X POST \
  --header "PRIVATE-TOKEN: <gitlab-token>" \
  "http://gitlab.94ai.pro/api/v4/projects/<project-path>/pipelines/<pipeline-id>/cancel"
```

---

## 注意事项

### 安全规范
- ❌ **禁止**在日志或输出中暴露完整的 token
- ❌ **禁止**将 token 提交到代码仓库
- ✅ **建议**使用项目级别的 token 而非个人 token
- ✅ **建议**定期轮换 token

### Token 管理
- Token 存储位置：项目配置或环境变量
- Token 权限：需要 `api` 权限
- Token 有效期：根据 GitLab 设置
- **重要**：在实际使用时，需要向用户询问 token 或从安全的配置中获取，不要在代码或文档中硬编码 token

### 获取 Token 的方式
1. **询问用户**：在执行技能时询问用户提供 token
2. **环境变量**：从环境变量中读取（如 `GITLAB_TOKEN`）
3. **配置文件**：从项目的配置文件中读取
4. **GitLab 设置**：用户可以在 GitLab 的 User Settings > Access Tokens 中生成新的 token

### 触发规则理解

根据项目的 `.gitlab-ci.yml` 配置（第 59-62 行）：

```yaml
.trigger_rule: &trigger_rule
  if: $CI_PIPELINE_SOURCE != "web" && $CI_PIPELINE_SOURCE != "schedule" && $CI_COMMIT_BRANCH !~ /^develop.*/ && $CI_PIPELINE_SOURCE != "api"
  when: never
```

**自动触发条件**：
- ✅ Web UI 手动触发
- ✅ API 触发（本技能使用的方式）
- ✅ 定时触发
- ✅ develop 开头的分支 push

**不会自动触发**：
- ❌ test 分支的普通 push
- ❌ feature 分支的普通 push
- ❌ 其他非 develop 分支的 push

这就是为什么需要使用 API 或 Web UI 手动触发的原因。

---

## 错误处理

### 场景 1：Token 无效或过期
```
HTTP 401 Unauthorized

解决方案：
1. 检查 token 是否正确
2. 确认 token 是否过期
3. 确认 token 是否有 api 权限
4. 重新生成 token
```

### 场景 2：项目路径错误
```
HTTP 404 Not Found

解决方案：
1. 确认项目路径是否正确
2. 确认路径是否正确 URL 编码（/ 编码为 %2F）
3. 确认用户是否有项目访问权限
```

### 场景 3：分支不存在
```
{"message": "Reference not found"}

解决方案：
1. 确认分支名称是否正确
2. 运行 git branch -a 查看所有分支
3. 确认分支是否已推送到远程
```

### 场景 4：Pipeline 创建失败
```
{"message": "Failed to create pipeline"}

解决方案：
1. 检查 .gitlab-ci.yml 语法是否正确
2. 查看 GitLab CI/CD 设置是否启用
3. 检查是否有足够的 Runner 可用
```

### 场景 5：触发规则阻止 API 触发
```
{"message":{"base":["Pipeline will not run for the selected trigger. The rules configuration prevented any jobs from being added to the pipeline."]}}

原因：
项目的 .gitlab-ci.yml 中的 .trigger_rule 阻止了 API 触发

解决方案：
修改 .gitlab-ci.yml 文件，在 .trigger_rule 中添加 API 触发支持：

```yaml
.trigger_rule: &trigger_rule
  if: $CI_PIPELINE_SOURCE != "web" && $CI_PIPELINE_SOURCE != "schedule" && $CI_COMMIT_BRANCH !~ /^develop.*/ && $CI_PIPELINE_SOURCE != "api"
  when: never
```

关键是添加 `&& $CI_PIPELINE_SOURCE != "api"` 条件，这样当来源是 api 时，条件不满足，就不会执行 `when: never`，pipeline 就可以运行。

修改后需要提交并推送到远程，然后重新触发 pipeline。
```

---

## 扩展功能

### 等待 Pipeline 完成

触发后可以轮询状态直到完成：

```bash
# 循环查询直到完成
while true; do
  status=$(curl -s --header "PRIVATE-TOKEN: <token>" \
    "http://gitlab.94ai.pro/api/v4/projects/<project>/pipelines/<id>" \
    | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

  echo "当前状态: $status"

  if [ "$status" = "success" ] || [ "$status" = "failed" ]; then
    break
  fi

  sleep 10
done
```

### 查看 Pipeline Jobs

查看 pipeline 包含的所有 jobs：

```bash
curl --header "PRIVATE-TOKEN: <token>" \
  "http://gitlab.94ai.pro/api/v4/projects/<project>/pipelines/<id>/jobs"
```

### 查看 Job 日志

查看特定 job 的执行日志：

```bash
curl --header "PRIVATE-TOKEN: <token>" \
  "http://gitlab.94ai.pro/api/v4/projects/<project>/jobs/<job-id>/trace"
```

---

## 示例对话

**用户**: "帮我构建一下"

**助手行为**:
1. 检查环境变量 `GITLAB_TOKEN` 是否存在
2. 如果存在，直接使用；如果不存在，询问用户提供
3. 并行运行 `git branch --show-current`、`git remote -v`、`git log --oneline -3`
4. 从 `git remote -v` 提取项目路径并 URL 编码
5. 检查 `.gitlab-ci.yml` 确认是否需要指定模块
6. 使用 API 触发当前分支的 pipeline
7. 解析返回的 JSON 响应
8. 向用户报告 pipeline ID、状态和查看链接
9. 如果用户提供了新 token，询问是否保存到环境变量

**用户**: "触发 test 分支的 pipeline"

**助手行为**:
1. 并行运行 `git branch --show-current`、`git remote -v`、`git log --oneline -3`
2. 从 `git remote -v` 提取项目路径并 URL 编码
3. 使用 API 触发 test 分支的 pipeline
4. 解析返回的 JSON 响应
5. 向用户报告 pipeline ID、状态和查看链接

**用户**: "触发 server 模块到测试环境"

**助手行为**:
1. 检查当前分支
2. 查看 `.gitlab-ci.yml` 确认 SUB_MODULE 选项
3. 使用 API 触发 pipeline，带变量：
   - `SUB_MODULE=server`（或项目实际的模块名）
   - `ENVIRONMENT_NAME=test`
4. 报告触发结果

**用户**: "API 触发失败，提示规则阻止"

**助手行为**:
1. 读取 `.gitlab-ci.yml` 文件
2. 检查 `.trigger_rule` 配置
3. 如果缺少 `&& $CI_PIPELINE_SOURCE != "api"` 条件，修改文件
4. 提交并推送修改
5. 重新触发 pipeline

---

## 相关技能

- `merge-to-test`: 合并代码到 test 分支后可能需要触发 pipeline
- `commit-cn`: 提交代码后可能需要触发 pipeline
- `verification-before-completion`: 部署前验证代码质量

---

## GitLab API 参考

- 触发 Pipeline: `POST /projects/:id/pipeline`
- 查询 Pipeline: `GET /projects/:id/pipelines/:pipeline_id`
- 取消 Pipeline: `POST /projects/:id/pipelines/:pipeline_id/cancel`
- 重试 Pipeline: `POST /projects/:id/pipelines/:pipeline_id/retry`
- 查询 Jobs: `GET /projects/:id/pipelines/:pipeline_id/jobs`

完整文档：https://docs.gitlab.com/ee/api/pipelines.html
