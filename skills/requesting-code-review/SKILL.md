---
name: requesting-code-review
description: 完成任务或实现主要功能后使用，仅做代码审查，不执行合并操作
---

# 请求代码审查

在问题扩散前捕获它们，确保代码质量和生产就绪性。仅执行代码审查，不进行任何合并操作。

**核心原则：** 早审查，常审查。只审查，不合并。

## 何时请求审查

**强制性：**
- 完成主要功能后
- 涉及数据库变更时
- 跨服务调用变更时

**可选但有价值：**
- 遇到困难时（获得新视角）
- 重构前（基线检查）
- 修复复杂 bug 后
- 跨服务调用变更时

## 如何请求

**1. 确定审查范围：**

首先获取最新的远程分支信息：

```bash
# 获取最新的远程分支
git fetch origin
```

然后根据你的工作流选择合适的 base commit：

```bash
# 场景 1：审查当前分支的所有变更（对比 main）
BASE_SHA=$(git merge-base HEAD origin/main)
HEAD_SHA=$(git rev-parse HEAD)

# 场景 2：审查最近的几次提交
BASE_SHA=$(git rev-parse HEAD~3)  # 最近 3 次提交
HEAD_SHA=$(git rev-parse HEAD)

# 场景 3：审查某个功能分支（对比 test）
BASE_SHA=$(git merge-base HEAD origin/test)
HEAD_SHA=$(git rev-parse HEAD)

# 场景 4：审查特定提交范围
BASE_SHA=<起始提交SHA>
HEAD_SHA=<结束提交SHA>

# 场景 5：对比最新的 release 分支（了解相对于生产环境的所有变更）
# 找到最新的 release 分支
LATEST_RELEASE=$(git branch -r | grep "origin/release_20" | grep -E "release_[0-9]{8}$" | sort | tail -1)
# 对比当前分支与最新 release 分支
git log --oneline $LATEST_RELEASE..HEAD
git diff $LATEST_RELEASE...HEAD
```

**说明**：
- 先执行 `git fetch origin` 获取最新的远程分支信息
- 使用 `git branch -r | grep ... | tail -1` 找到最新的 release 分支名
- 对比最新 release 分支有助于了解当前分支相对于生产环境的所有变更
- 这对于合并到 test 分支前的审查特别重要

**2. 查看变更概览：**

```bash
# 查看变更的文件列表
git diff --stat $BASE_SHA..$HEAD_SHA

# 查看详细变更
git diff $BASE_SHA..$HEAD_SHA
```

**3. 执行代码审查：**

直接要求 Claude 按照 `code-reviewer.md` 模板进行审查，提供以下信息：

- **已实现内容**：简要描述你做了什么
- **需求/计划**：参考的需求文档或计划
- **Git 范围**：BASE_SHA 和 HEAD_SHA
- **特别关注点**（可选）：需要重点审查的部分

**4. 根据反馈行动：**

- 立即修复 **Critical（严重）** 问题
- 继续前修复 **Important（重要）** 问题
- 记录 **Minor（次要）** 问题稍后处理
- 如果审查结果有误，用技术理由说明

## 示例

### 示例 1：审查新增企业配置字段

```
用户：我刚完成了在企业配置中新增 maxRetryCount 字段，请帮我审查代码。

Claude：
[执行 git 命令获取变更范围]
BASE_SHA=$(git merge-base HEAD origin/main)
HEAD_SHA=$(git rev-parse HEAD)

[查看变更文件]
git diff --stat $BASE_SHA..$HEAD_SHA

[按照 code-reviewer.md 模板进行审查]

已实现内容：在新旧企业配置系统中新增 maxRetryCount 字段
需求：支持配置企业级别的最大重试次数
Git 范围：a7981ec..3df7661

### 审查结果

#### 优点
- EnterpriseConfig.java 和 EnterpriseConfigDO.java 字段定义一致
- JSON 转换逻辑正确处理了新字段
- DDL 脚本包含了默认值和注释

#### 问题

##### Important
1. **缺少字段校验**
   - 文件：EnterpriseConfigService.java:156
   - 问题：maxRetryCount 未校验范围，可能设置负数或过大值
   - 修复：添加 @Min(0) @Max(10) 注解，或在 Service 层校验

##### Minor
1. **缺少单元测试**
   - 影响：新字段的 JSON 转换未覆盖测试
   - 建议：在 EnterpriseConfigTest 中添加测试用例

#### 评估
**代码质量评级：需修复**
**理由：** 核心实现正确，但缺少必要的字段校验，可能导致运行时错误。
```

### 示例 2：审查 Feign Client 调用变更

```
用户：我修改了用户服务的 Feign Client 调用，增加了超时配置，请审查。

Claude：
[执行审查流程]

### 审查结果

#### 优点
- Feign Client 超时配置合理（连接 3s，读取 10s）
- 添加了熔断降级逻辑

#### 问题

##### Critical
1. **降级方法返回值不安全**
   - 文件：UserServiceFallback.java:23
   - 问题：降级方法返回 null，调用方未做空指针检查
   - 修复：返回空对象或抛出业务异常

##### Important
1. **缺少日志记录**
   - 文件：UserServiceFallback.java:20-25
   - 问题：降级触发时无日志，无法追踪问题
   - 修复：添加 log.error 记录降级原因和参数

#### 评估
**代码质量评级：不通过**
**理由：** 降级方法返回 null 可能导致 NPE，必须修复后才能通过审查。
```

## 与现有技能集成

**与 commit-cn 配合：**
1. 完成代码变更
2. 请求代码审查
3. 修复审查发现的问题
4. 使用 `/commit-cn` 提交代码

**与 release-doc-generator 配合：**
1. 审查发版分支的所有变更
2. 确认 SQL、配置变更都已审查
3. 生成发版文档

**注意：本技能仅负责代码审查，不执行任何合并操作。如需合并，请使用 `/merge-to-test` 或 `/commit-and-deploy` 等技能。**

## 危险信号

**绝不：**
- 因为"很简单"而跳过审查
- 忽略 Critical 问题
- 数据库变更未经审查就执行
- 跨服务调用变更未审查降级逻辑
- 在审查过程中执行合并操作

**如果审查结果有误：**
- 用技术理由说明（如：框架保证、业务逻辑保证）
- 提供代码或测试证明
- 请求重新评估

## Java 微服务特别关注点

审查时应特别关注：

1. **Spring Bean 管理**：注入方式、生命周期、循环依赖
2. **事务边界**：@Transactional 位置、传播行为、异常回滚
3. **MyBatis SQL**：SQL 注入风险、索引使用、N+1 查询
4. **Feign Client**：超时配置、熔断降级、重试策略
5. **线程安全**：共享变量、并发集合、锁使用
6. **异常处理**：业务异常、系统异常、全局异常处理
7. **配置管理**：配置中心、环境隔离、敏感信息
8. **日志规范**：日志级别、敏感信息脱敏、链路追踪
9. **循环中的远程调用**：Redis 查询、数据库查询、HTTP 调用（见下文详细说明）

### 循环中的远程调用（Critical 级别问题）

**问题模式：** 在 for 循环中重复调用 Redis、数据库或远程服务，导致严重性能问题。

**典型场景：**

```java
// ❌ 错误示例：在循环中重复查询 Redis
for (AutoDialerNumberDto dto : list) {
    List<AutoDialerChat> chats = callMap.get(dto.getCallid());
    for (AutoDialerChat chat : chats) {
        // 每次迭代都查询 Redis 获取企业配置
        String timeZone = TimeZoneRepository.getTimeZoneIdByCompanyId(companyId);
        AppAuthConfig config = AiAppAuthRepository.getAppAuthConfig(companyId);
        // ... 使用配置
    }
}
// 性能：N × M 次 Redis 查询（N=dto数量，M=每个dto的对话数）
```

**正确做法：**

```java
// ✅ 正确示例：提前查询，循环中复用
// 在循环外查询一次
String timeZone = TimeZoneRepository.getTimeZoneIdByCompanyId(companyId);
AppAuthConfig config = AiAppAuthRepository.getAppAuthConfig(companyId);
TimeZoneConfig timeZoneConfig = new TimeZoneConfig(timeZone, config);

for (AutoDialerNumberDto dto : list) {
    List<AutoDialerChat> chats = callMap.get(dto.getCallid());
    for (AutoDialerChat chat : chats) {
        // 直接使用预先查询的配置
        Date convertedTime = convertTime(chat.getCreateTime(), timeZoneConfig);
        // ...
    }
}
// 性能：1 次 Redis 查询
```

**审查检查点：**

1. **识别循环中的远程调用**
   - 搜索 `for`/`while` 循环内的方法调用
   - 检查方法名包含：`get*ByCompanyId`、`query*`、`find*`、`*Repository.*`、`*Cache.*`
   - 特别关注嵌套循环（性能影响呈指数级）

2. **评估性能影响**
   - 单层循环：N 次调用（N=循环次数）
   - 嵌套循环：N × M 次调用（严重性能问题）
   - 计算最坏情况：如果 N=1000，M=100，则 100,000 次 Redis 查询

3. **修复方案**
   - 提取到循环外：适用于所有迭代使用相同参数
   - 批量查询：适用于需要查询多个不同 ID（如 `selectByIds(List<Integer> ids)`）
   - 缓存结果：适用于循环内有条件查询（使用 `Map<Key, Value>` 缓存）

**真实案例：**

```
问题：AutoDialerNumberRepository.formatExportChats 在嵌套循环中调用
      TimeZoneRepository.chinaTzToOtherCountryTzCompanyConfig
影响：导出 1000 条外呼记录（每条 50 条对话）时，产生 50,000 次 Redis 查询
修复：将时区配置查询提取到最外层循环前，性能提升 50,000 倍
文件：ai-domain/src/main/java/com/tkylin/ycloud/domain/repository/AutoDialerNumberRepository.java:3340-3387
```

**其他常见场景：**

- 循环中调用 Feign Client（跨服务调用）
- 循环中执行数据库查询（未使用批量接口）
- 循环中读取 Nacos 配置
- 循环中调用第三方 API

参见模板：requesting-code-review/code-reviewer.md
