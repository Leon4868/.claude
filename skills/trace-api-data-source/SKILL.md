---
name: trace-api-data-source
description: 追踪接口逻辑和数据来源的全链路分析方法。包含确定服务与入口、分析业务逻辑、追踪远程调用、深入数据库层、特殊场景分析（缓存/异步/MQ）、反向追踪的完整流程。适用于需要分析接口业务逻辑和定位数据源（跨服务调用、数据库查询、配置读取及缓存等）的场景。
---

# 接口数据源追踪

本 Skill 用于全链路分析接口业务逻辑，定位数据源（涵盖跨服务调用、数据库查询、配置读取及缓存等场景）。

## 使用方式

当需要分析接口业务逻辑和定位数据来源时，参考以下步骤。

## 执行步骤

### 1. 确定服务与入口 (Service & Controller)

**利用 URL 识别服务**: 参考 `find-service-by-url` Skill 确定代码所在的微服务仓库（如 `company-aggre`, `data-center`, `ai-service` 等）。

**定位 Controller**:
- 在对应仓库中，根据 URL 路径（如 `/api/task/list`）全局搜索 `@RequestMapping`, `@PostMapping`, `@GetMapping`
- **重复 Controller 处理**:
  - 如果找到同名的 Controller (e.g. `ai-admin` vs `ai-decision-system`)，需要确认路由配置
  - **JFinal**: 检查 `Routes.java` 或 `AppConfig.java` 确认哪个 Controller 注册了该路径
- **提示**: 聚合层服务（如 `company-aggre`）通常只做转发和简单组装，核心逻辑往往在下游的基础服务（如 `ai-service`）

### 2. 分析业务逻辑 (Service Layer)

进入 `ServiceImpl` 分析核心流程。

**方法定位技巧**:
- 对于大文件，使用代码搜索工具获取准确行号

**关键模式识别**:
- **本地查询**: 调用 `Dao/Mapper/Repository`
- **远程调用**: 调用 `*Client` (Feign Client)
- **配置读取**: 调用 `*ConfigService` (如 `SdConfigService`)，数据可能来自配置中心或配置表，而非业务主表
- **策略/工厂模式**: 如果代码中出现 `StrategyHolder.getStrategy(...)` 或 `Factory.create(...)`，实际逻辑在具体的实现类中（例如 `XShield` 的拦截策略），需根据上下文（如 `type` 字段）找到通过 `@Component("具体名称")` 定义的实现类

### 3. 追踪远程调用 (Feign Client)

当遇到 `client.method()` 调用时：

**确定目标服务**: 查看 Client 接口上的 `@FeignClient(name = "service-name")`，确定下游服务名

**查找下游接口**:
- 复制 Client 方法上的 URL 路径（例如 `/v1/inner/task/query`）
- 在目标服务代码中搜索该路径
- **注意**: Feign 接口定义的路径可能与 Controller 实际路径不完全一致（有时会有 `context-path` 差异），可以尝试只搜索路径的后半部分关键字

### 4. 深入数据库层 (DAO/Mapper & MyBatis Plus)

**MyBatis Plus (MP)**:
- 如果是 `baseMapper.selectList(wrapper)` 或 `service.list(wrapper)`
- **重点分析 Wrapper**: 仔细查看代码中 `QueryWrapper` 或 `LambdaQueryWrapper` 的构建过程，这是**最核心的过滤逻辑**来源（对应 SQL 的 `WHERE` 子句）

**Legacy iBatis/MyBatis (XML)**:
- **无注解接口**: 如果 DAO/Repository 接口没有任何 SQL 注解
- **查找 XML**: 在 `src/main/resources` 下查找 `sqlmap` 或 `mapper` 目录
- **文件名约定**: 通常为 `*SqlMap.xml` 或 `*Mapper.xml`
- **命名空间**: XML 中的 `namespace` 通常对应 DAO 接口所在的包名或接口名（例如 namespace="ai_template" 对应 ai_template_SqlMap.xml）

**XML Mapper (Complex)**:
- 如果调用了自定义方法（如 `mapper.selectCustomData`），需跳转到 `resources/mapper` 下对应的 XML 文件
- 检查 XML 中的 `<if test="...">` 动态 SQL 标签，确认不同参数下的查询差异

**分表场景**:
- 注意检查实体类上的 `@TableName`。如果涉及分表（如按月分表 `t_record_202310`），代码中可能会有动态表名处理逻辑，或者通过 `ShardingSphere` 隐式处理

### 5. 特殊场景分析

**缓存 (Redis/LocalCache)**:
- 如果代码中出现 `@Cached`, `RedisTemplate.opsForValue().get()`, `RedissonClient`
- **数据源头**: 缓存只是搬运工。必须找到**写入缓存**的地方（`write` / `put`）来确定原始数据来源
- **搜索技巧**: 搜索 Redis Key 的前缀字符串，找到所有引用该 Key 的代码

**异步数据 (MQ/Job)**:
- 如果数据库字段由异步任务写入（如"昨天消耗金额"）
- **MQ**: 搜索 `Listener` 或 `Consumer` 类，查看消息处理逻辑
- **定时任务**: 搜索 `@Scheduled` 或 `XxlJob` 处理器，查看定时聚合逻辑

### 6. 反向追踪 (从结果找来源)

如果知道数据库中的某个字段值不对（如 `total_amount`），但也找不到写入点：

- **搜索 Setter**: 全局搜索 `.setTotalAmount(` 或 `.set("total_amount", ...)`
- **搜索 SQL**: 全局搜索 `update table set ... total_amount = ...`

### 7. 验证总结

确认并绘制数据流向图：`Request -> Aggregation Service -> Core Service -> Logic/Strategy -> Mapper -> DB/Cache`
