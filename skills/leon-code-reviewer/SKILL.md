---
name: leon-code-reviewer
description: 两轮代码审查 + 安全扫描，发现安全问题时通过 Telegram 通知并等待审批
---

# leon-code-reviewer — 代码审查与安全扫描

对变更代码进行两轮质量审查和安全扫描。安全问题会触发 Telegram 通知。

## 输入

- 变更的文件列表（通过 `git diff --name-only` 获取）
- Feature 名称和 specs 路径

## 执行步骤

### 1. 收集变更

```bash
git diff --name-only HEAD
git diff HEAD
```

如果没有 git 变更，则对比 specs 中 tasks.md 涉及的文件。

### 2. 第 1 轮审查：代码质量

逐文件检查：
- **风格一致性**: 对照 `.claude/rules/coding-style.md`
- **类型安全**: 是否有 any、类型断言过多、缺少类型定义
- **逻辑正确性**: 边界条件、空值处理、错误处理
- **命名规范**: 变量/函数/组件命名是否清晰

输出审查结果，标注 `[PASS]` `[WARN]` `[FAIL]`。

### 3. 第 2 轮审查：架构与性能

- **架构一致性**: 是否符合 design.md 中的设计方案
- **模块边界**: 是否有不合理的跨模块依赖
- **性能**: 是否有明显的性能问题（不必要的重渲染、大循环、内存泄漏风险）
- **可维护性**: 代码是否易于理解和修改

### 4. 安全扫描

读取 `.claude/rules/security.md`，逐项扫描：

**必检项：**
- [ ] 硬编码的密钥、Token、密码、API Key
- [ ] 使用 `dangerouslySetInnerHTML` 未清洗输入
- [ ] URL 中传递敏感参数
- [ ] `eval()`、`new Function()` 等动态执行
- [ ] 环境变量使用是否正确（VITE_ 前缀）
- [ ] 敏感文件是否被 .gitignore 覆盖
- [ ] 第三方依赖是否有已知漏洞（npm audit）
- [ ] XSS 注入风险
- [ ] CSRF 防护（如适用）
- [ ] SQL 注入（如适用）

### 5. 结果处理

#### 安全扫描通过 ✅

```
[SECURITY SCAN] ✅ PASSED
- 扫描文件数: N
- 检查规则数: N
- 未发现安全问题
```

继续流水线下一步。

#### 安全扫描发现问题 ❌

**立即通过 Telegram 发送通知：**

使用 `mcp__plugin_telegram_telegram__reply` 工具，向关联的 TG chat 发送：

```
🚨 安全扫描警告 — {项目名}/{feature-name}

发现 {N} 个安全问题：

1. [{严重程度}] {问题描述}
   📄 文件: {file_path}:{line}
   💡 建议: {修复建议}

2. ...

请回复:
- /approve — 确认已知风险，继续流水线
- 或直接给出修复指示
```

然后 **暂停流水线**，等待用户通过 TG 回复：
- 收到 `/approve` → 记录审批，继续流水线
- 收到修复指示 → 返回给调用者，触发修复流程

#### 代码质量问题（非安全）

如果只有代码质量问题（无安全问题）：
- 自动修复可修复的问题
- 重新审查（最多 3 轮）
- 3 轮后仍有问题则报告给用户

## 输出

```markdown
## 审查报告

### 第 1 轮：代码质量
- 审查文件数: N
- PASS: N | WARN: N | FAIL: N
- {具体问题列表}

### 第 2 轮：架构与性能
- {具体问题列表}

### 安全扫描
- 状态: PASSED / FAILED
- {问题列表（如有）}

### 总结
- 审查结果: {APPROVED / NEEDS_FIX / SECURITY_HOLD}
```
