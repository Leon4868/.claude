---
name: add-legacy-query-param
description: 在旧的 iBatis/CustomDAO 架构中新增查询参数的标准化流程。包含确认需求定位代码、修改请求对象、修改数据访问层（DAO接口/实现类/SQL映射）、修改Repository/Service层的完整步骤。适用于使用 iBatis SqlMap 和 CustomDAO 模式的 Legacy 项目。
---

# 在 Legacy 项目 (iBatis + CustomDAO) 中新增查询参数

本 Skill 指导如何在当前架构下（使用 iBatis SqlMap 和 CustomDAO 模式）为现有接口添加新的查询参数（如模糊搜索）。

## 使用方式

当需要在 Legacy 项目中新增查询参数时，参考以下流程。

## 执行步骤

### 1. 确认需求与定位代码

- 确定需要修改的 API 接口 URL
- 定位对应的 Controller 方法
- 找到该方法调用的 Repository 或 Service 方法
- 找到使用的数据访问对象 (DAO)
  - **重要**: 确认是否为 `CustomDAO`。如果是生成的 Base DAO，**不要修改**生成的 `SqlMap.xml`，应在 `CustomDAO` 中扩展或修改

### 2. 修改请求对象 (Request DTO)

- 找到对应的 Request DTO 类 (通常在 `domain` 模块)
- 添加新字段（如 `private String brandName;`）
- 添加 Getter 和 Setter 方法

### 3. 修改数据访问层 (DAO Layer)

#### 3.1 修改接口 (Interface)
- 找到 `CustomDAO` 接口 (如 `AiCompanyCustomDAO.java`)
- 更新查询方法签名，添加新参数

#### 3.2 修改实现类 (Implementation)
- 找到 `CustomDAOImpl` 类 (如 `AiCompanyCustomDAOImpl.java`)
  - 此类通常继承 `SqlMapDaoTemplate`
- 更新方法实现：
  - 将新参数放入 `Map<String, Object> params`
  - **注意**: 处理参数格式
    - 如果是模糊搜索，且 XML 中使用 `LIKE $param$`，需在 Java 代码中处理通配符：`params.put("paramName", "'%" + value + "%'");` (注意包含单引号)
    - 如果是精确匹配或 XML 中使用 `#param#`，直接 put 值即可

#### 3.3 修改 SQL 映射 (SqlMap XML)
- 找到 `src/main/resources/sqlmap/custom` 目录下的对应 `_custom_SqlMap.xml` 文件
- 更新 `select` 语句的 `<dynamic>` 块
  - 添加 `<isNotEmpty>` 或 `<isNotNull>` 判断
  - 编写 SQL 片段，例如：
    ```xml
    <isNotEmpty prepend="and" property="paramName">
        column_name like $paramName$
    </isNotEmpty>
    ```

### 4. 修改 Repository/Service 层

- 找到调用 DAO 的 Repository 类 (如 `SettlementRecordsRepository.java`)
- 更新调用代码，将 DTO 中的新字段传递给 DAO 方法

### 5. 验证与注意事项

- **不要修改生成的代码**: 永远不要修改 `ibatorgenerated` 生成的 Entity 和 Base `SqlMap.xml`，除非数据库表结构发生根本性变化
- **SQL 注入风险**: 使用 `$` 占位符时需格外小心，确保输入值经过处理或验证
- **参数 Key 匹配**: Java Map 中的 Key 必须与 XML 中的 property 名称完全一致
