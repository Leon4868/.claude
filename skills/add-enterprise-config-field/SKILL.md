---
name: add-enterprise-config-field
description: 在新旧企业配置中新增配置字段的完整流程。包含涉及7个文件的修改步骤、不同字段类型的处理方式（String/Integer/List/SwitchEnum）、JSON转换逻辑、DDL脚本模板。使用于需要在企业配置系统中添加新配置字段的场景。
---

# 企业配置新增字段流程

本 Skill 指导如何在新旧企业配置系统中新增一个配置字段。

## 使用方式

当需要新增企业配置字段时，使用以下 prompt 模板：

```
在新旧企业配置中新增一个字段：「字段描述」

字段信息：
- 字段名称：fieldName（驼峰命名）
- 字段类型：String / Integer / List<Integer> / List<String> / SwitchEnum 等
- 字段说明：[描述字段的作用和用途]

需要同步新旧两个系统。
```

## 涉及的文件（共 7 个）

### 1. 旧表 JSON 配置
- `ai-service/api/src/main/java/com/ai94/ai/service/api/response/AppAuthConfig.java`
  - 新增字段定义

### 2. 新表配置对象
- `company/core/src/main/java/com/ai94/company/dal/entity/PersonalityConfig.java`
  - 新增实体字段，如果是复杂类型需用 JSON 字符串存储
  
- `company/api/src/main/java/com/ai94/company/api/response/PersonalityConf.java`
  - 新增 Response 字段
  
- `company/api/src/main/java/com/ai94/company/api/dto/PersonalityConfigDto.java`
  - 新增 DTO 字段（`SyncPersonalityConfigDto` 继承此类，无需单独修改）
  - **重要**：新增的配置字段通常是可选的，不要添加 `@NotNull` 验证
  - 只添加 `@Schema(description = "字段说明")` 注解即可，不需要 `requiredMode = RequiredMode.REQUIRED`

### 3. 字段转换
- `company/core/src/main/java/com/ai94/company/transfer/config/PersonalityConfigTransfer.java`
  - 在 `toResponse` 方法中添加 JSON → List 转换（如需要）
  - 在 `copy` 方法的 `@Mapping` 中添加 `ignore = true`（如需要）
  - 在 `dtoToModel` 和 `syncDtoToModel` 的 `@Mapping` 中添加 List → JSON 转换（如需要）

### 4. 同步逻辑
- `company-aggre/core/src/main/java/com/ai94/company/aggre/service/SyncConfigService.java`
  - `oldToNewForPersonality` 方法：从 `AppAuthConfig` 读取设置到 `SyncPersonalityConfigDto`
  - `newToOldForPersonality` 方法：从 `PersonalityConf` 读取设置到 `AppAuthConfig`

### 5. DDL 脚本
- `company/doc/ddl/add_{field_name}.sql`
  - ALTER TABLE 语句添加新列

## 字段类型处理

| 字段类型 | AppAuthConfig | PersonalityConfig | PersonalityConf / Dto | Transfer 处理 |
|---------|---------------|-------------------|----------------------|---------------|
| String | String | String | String | 无需特殊处理 |
| Integer | Integer | Integer | Integer | 无需特殊处理 |
| SwitchEnum | Integer | SwitchEnum | SwitchEnum | 使用 `SwitchEnum.covert()` |
| List<T> | List<T> | String (JSON) | List<T> | 需要 JSON 转换 |

## DDL 模板

```sql
ALTER TABLE t_sd_personality_config 
ADD COLUMN {column_name} {data_type} DEFAULT NULL 
COMMENT '{字段说明}';
```

| 字段类型 | 推荐 SQL 类型 |
|---------|--------------|
| String | VARCHAR(255) |
| Integer | INT(11) |
| SwitchEnum | TINYINT(1) |
| List (JSON) | VARCHAR(500) 或 TEXT |

## 注意事项

### 验证注解使用规则
- **新增配置字段通常不需要 `@NotNull` 验证**，因为：
  1. 新增字段是可选的，旧数据可能没有这个值
  2. 数据库字段通常设置为 `DEFAULT NULL` 或有默认值
  3. 代码中会使用 `Optional.ofNullable().orElse(默认值)` 处理 null 情况

- **只在以下情况添加 `@NotNull`**：
  1. 字段是系统核心配置，必须有值才能正常运行
  2. 前端表单明确要求用户必填
  3. 与产品经理确认该字段为必填项

- **正确的注解写法**：
  ```java
  // 可选字段（推荐用于新增配置）
  @Schema(description = "字段说明")
  private SwitchEnum fieldName;

  // 必填字段（谨慎使用）
  @NotNull(message = "#{字段说明}")
  @Schema(description = "字段说明", requiredMode = RequiredMode.REQUIRED)
  private SwitchEnum fieldName;
  ```

### 默认值处理
- 新增配置字段应该考虑向后兼容性，设置合理的默认值
- 在登录逻辑或使用配置的地方，使用 `Optional.ofNullable().orElse(默认值)` 处理
- DDL 脚本中可以设置 `DEFAULT` 值，确保数据库层面的默认值