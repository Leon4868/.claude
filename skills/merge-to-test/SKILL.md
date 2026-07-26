---
name: merge-to-test
description: 将当前分支合并到 test 分支并推送到远程，用于测试环境部署
---

# merge-to-test

将当前分支合并到 test 分支并推送到远程，用于测试环境部署

**适用场景**: 当用户要求将代码合并到 test 分支、推送到测试环境，或需要在测试环境验证功能时使用

**触发短语**: "合并到test"、"推送到test"、"部署到测试环境"、"merge to test"

---

## 工作流程

当用户请求将代码合并到 test 分支时，按以下步骤执行：

### 1. 检查当前状态

并行运行以下命令了解当前状态：

```bash
# 查看当前分支名称
git branch --show-current

# 查看工作区状态
git status

# 查看当前分支的提交历史
git log --oneline -5
```

**验证点**：
- 确认当前不在 test 分支上
- 确认没有未提交的变更（如有，提示用户先提交）
- 记录当前分支名称用于后续合并

### 2. 切换到 test 分支并更新

> ⚠️ **必须先切换到 test 分支，再执行 pull。绝对禁止在功能分支上执行 `git pull origin test`，否则会将 test 分支合并到功能分支，污染功能分支的提交历史。**

```bash
# 先切换到 test 分支
git checkout test

# 再拉取 test 分支最新代码
git pull origin test
```

**说明**：
- 必须先 checkout 到 test，再 pull，顺序不能颠倒
- 如果 test 分支不存在，提示用户确认分支名称

### 3. 合并功能分支

```bash
# 使用 --no-ff 创建合并提交（保留分支历史）
git merge <feature-branch-name> --no-ff
```

**合并策略**：
- 使用 `--no-ff` 标志创建明确的合并提交
- 保留完整的分支历史，便于追溯
- 如果出现冲突，**立即中止合并并切回原分支**，由用户自行解决

**冲突处理（严格规则）**：

> ⚠️ **绝对禁止 Claude 自行解决任何合并冲突。** 无论冲突多简单，都必须交给用户处理。

如果 `git merge` 命令的退出码非 0 或输出中包含 `CONFLICT`：

1. 立即运行 `git merge --abort` 中止合并
2. 切换回原功能分支：`git checkout <feature-branch-name>`
3. 向用户报告冲突信息，**停止所有后续操作**（不再执行验证、推送等步骤）
4. 提示用户手动解决：
   ```
   ❌ 合并到 test 分支时出现冲突，已自动中止合并并切回原分支。

   冲突文件：
   - [列出冲突文件]

   请手动解决冲突后重新运行此技能：
   1. git checkout test
   2. git merge <feature-branch-name> --no-ff
   3. 手动编辑冲突文件，解决所有冲突标记（<<<<<<< / ======= / >>>>>>>）
   4. git add <resolved-files>
   5. git commit
   6. git push origin test
   7. git checkout <feature-branch-name>

   或者你解决完冲突后再次告诉我"合并到test"，我会重新执行。
   ```
5. **不要尝试读取冲突文件内容、不要尝试编辑冲突文件、不要提供冲突解决建议**

### 4. 验证合并结果

```bash
# 查看合并后的状态
git status

# 查看最近的提交记录
git log --oneline -5

# 查看合并带来的变更
git diff HEAD~1
```

**验证点**：
- 确认合并提交已创建
- 确认本地 test 分支领先远程
- 检查变更内容是否符合预期

### 5. 推送到远程

```bash
# 推送到远程 test 分支
git push origin test
```

**推送后验证**：
```bash
# 确认推送成功
git status
```

### 6. 输出结果

向用户报告：
- ✅ 合并是否成功
- 📝 合并提交的哈希值和信息
- 📊 合并了哪些变更（文件数、行数）
- 🔄 推送状态（本地与远程是否同步）
- 🔗 GitLab/GitHub 链接（如果可用）

**输出示例**：
```
合并成功！

**合并结果**：
- ✅ 已将 `lwk/feature_20260228_抖店上传挽单结果` 合并到 `test` 分支
- 📝 合并提交：`41aaca5b0 Merge branch 'lwk/feature_20260228_抖店上传挽单结果' into test`
- 📊 变更内容：HangupHelper.java 新增 2 行代码（设置 config 字段）
- 🔄 已推送到远程 origin/test
- 🔗 GitLab: http://gitlab.94ai.pro/atomic/call-task
```

---

## 注意事项

### 安全规范
- ❌ **禁止**使用 `--force` 推送
- ❌ **禁止**在有未提交变更时执行合并
- ❌ **禁止**自动解决合并冲突（无论冲突多简单，一律中止合并交给用户）
- ❌ **禁止**读取、编辑冲突文件或提供冲突解决方案
- ❌ **禁止**在功能分支上执行 `git pull origin test`（会污染功能分支历史）
- ✅ **必须**先 `git checkout test`，再 `git pull origin test`，顺序不能颠倒
- ✅ **必须**使用 `--no-ff` 保留分支历史
- ✅ **必须**在推送前验证合并结果
- ✅ **必须**在冲突时执行 `git merge --abort` 并切回原分支

### 工作流程
- 只在用户明确要求时才执行合并和推送
- 如果当前分支有未提交的变更，先提示用户提交
- 如果出现合并冲突，停止操作并提示用户
- 合并前确认 test 分支是最新的
- 推送前验证合并提交是否正确

### 错误处理

**场景 1：当前分支有未提交变更**
```
检测到未提交的变更：
- [列出变更文件]

请先提交或暂存这些变更：
- 提交：使用 /commit-cn 技能
- 暂存：git stash
- 放弃：git checkout .
```

**场景 2：合并冲突**

> 遇到冲突时，Claude 必须立即中止合并并切回原分支，绝不尝试解决冲突。

```
❌ 合并到 test 分支时出现冲突，已自动中止合并并切回原分支 `<feature-branch-name>`。

冲突文件：
- path/to/file1.java
- path/to/file2.java

请手动解决冲突：
1. git checkout test
2. git merge <feature-branch-name> --no-ff
3. 编辑冲突文件，解决所有冲突标记
4. git add <resolved-files>
5. git commit
6. git push origin test
7. git checkout <feature-branch-name>

或者解决完冲突后再次告诉我"合并到test"。
```

**场景 3：推送失败**
```
推送失败，可能原因：
- 远程 test 分支有新提交
- 网络问题
- 权限不足

建议操作：
1. 拉取最新代码：git pull origin test
2. 重新推送：git push origin test
```

---

## 扩展功能

### 可选：切换回原分支

合并推送完成后，询问用户是否切换回原分支：

```bash
# 切换回功能分支
git checkout <original-branch-name>
```

### 可选：查看部署状态

如果项目配置了 CI/CD，可以查看部署状态：

```bash
# 查看最近的 CI/CD 流水线（GitLab）
# 需要根据实际项目配置调整
```

---

## 示例对话

**用户**: "把这个合并到test并推送"

**助手行为**:
1. 检查当前分支：`lwk/feature_20260228_抖店上传挽单结果`
2. 检查工作区状态：无未提交变更
3. 先切换到 test 分支（`git checkout test`），再拉取最新代码（`git pull origin test`）
4. 合并功能分支（使用 --no-ff）
5. 验证合并结果
6. 推送到远程
7. 切换回功能分支
8. 报告完整的合并和推送结果

---

## 相关技能

- `commit-cn`: 提交代码前使用
- `merge-to-release`: 合并到生产环境（如果有）
- `verification-before-completion`: 合并前验证代码质量
