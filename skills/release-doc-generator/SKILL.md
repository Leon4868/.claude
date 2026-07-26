---
name: release-doc-generator
description: 生成标准化的发版文档。当用户要求生成发版文档、上线文档、部署文档时使用此技能。此技能会自动从 git 分支、提交记录、SQL 变更脚本、代码 diff 中收集信息，分析跨服务依赖关系，生成包含发版顺序、SQL、配置变更、验证方案和回滚方案的 markdown 文档。
---

# 发版文档生成器

## 用途

根据当前项目的 git 信息和代码变更，自动生成标准化的发版文档。

## 触发时机

当用户要求"写发版文档"、"生成上线文档"、"发版清单"等类似请求时使用。

## 工作流程

### 第零步：定位服务目录

在执行任何 git 操作之前，必须先定位用户指定的服务实际目录位置。

#### 步骤 1：解析用户输入

用户可能以多种方式指定服务：
- 明确指定多个服务：\"涉及 tiktok-shop、call-task、constants 三个项目\"
- 只提到当前服务：\"写发版文档\"（默认当前目录）
- 提供完整路径：\"C:\\workspace\\call-task\"

#### 步骤 2：智能定位服务目录

**方法 A：用户明确指定服务列表**

如果用户明确列出了服务名称，对每个服务执行以下查找：

```bash
# 1. 首先检查当前目录是否就是目标服务
basename $(pwd)

# 2. 在父目录中查找兄弟目录
ls -d ../*服务名* 2>/dev/null

# 3. 在当前目录的子目录中查找
find . -maxdepth 2 -type d -name "*服务名*" 2>/dev/null

# 4. 检查是否为子模块（如 ai-quartz 是 ai-service 的子模块）
ls -d */服务名 2>/dev/null
```

**方法 B：用户未指定服务（默认当前服务）**

如果用户只说\"写发版文档\"，默认为当前目录的服务：

```bash
# 获取当前目录名作为服务名
basename $(pwd)

# 确认是否为 git 仓库
git rev-parse --is-inside-work-tree 2>/dev/null
```

**方法 C：交互式选择（推荐）**

如果自动定位不确定，使用 AskUserQuestion 工具让用户选择：

```json
{
  "questions": [{
    "question": "请选择要生成发版文档的服务",
    "header": "服务选择",
    "multiSelect": true,
    "options": [
      {"label": "call-task", "description": "呼叫任务服务（../call-task）"},
      {"label": "tiktok-shop", "description": "TikTok Shop 服务（../tiktok-shop）"},
      {"label": "constants", "description": "常量包（../constants）"}
    ]
  }]
}
```

#### 步骤 3：验证服务目录

对每个定位到的服务目录，执行验证：

```bash
# 进入目录
cd <服务路径>

# 验证是否为 git 仓库
git rev-parse --is-inside-work-tree 2>/dev/null

# 获取当前分支
git branch --show-current

# 获取远程仓库信息
git remote -v
```

**验证点**：
- ✅ 目录存在且可访问
- ✅ 是有效的 git 仓库
- ✅ 有远程仓库配置
- ❌ 如果验证失败，提示用户并跳过该服务

#### 步骤 4：记录服务映射

将定位结果记录下来，用于后续操作：

```
服务映射表：
- call-task → C:\workspace\call-task
- tiktok-shop → C:\workspace\tiktok-shop
- constants → C:\workspace\constants
```

**常见服务映射示例**：
| 用户输入 | 实际路径 | 说明 |
|---------|---------|------|
| ai-quartz | ai-service/quartz | 子模块 |
| company-server | ../company | 父目录的兄弟目录 |
| ai-admin | ./ai/ai-admin | 当前目录的子目录 |
| call-task | ../call-task | 父目录的兄弟目录 |

#### 步骤 5：处理特殊情况

**情况 A：服务名不完全匹配**
- 用户输入：\"company-server\"
- 实际目录：\"company\"
- 解决方案：使用模糊匹配 `find . -maxdepth 2 -type d -iname "*company*"`

**情况 B：子模块**
- 用户输入：\"ai-quartz\"
- 实际路径：\"ai-service/quartz\"
- 解决方案：检查子目录 `ls -d */quartz 2>/dev/null`

**情况 C：多个匹配**
- 找到多个可能的目录
- 解决方案：使用 AskUserQuestion 让用户选择正确的目录

**情况 D：找不到服务**
- 所有方法都找不到服务目录
- 解决方案：提示用户提供完整路径，或询问是否跳过该服务

### 第一步：拉取最新代码

在收集 Git 信息之前，必须先拉取最新的远程分支。

**对每个定位到的服务目录**（来自第零步的服务映射表），依次执行：

```bash
# 进入服务目录
cd <服务实际路径>

# 拉取最新的远程分支
git fetch --all

# 显示拉取结果
echo "✅ <服务名>: 已拉取最新代码"
```

**并行执行优化**（可选）：

如果有多个服务，可以并行拉取以节省时间：

```bash
# 服务 1
(cd ../call-task && git fetch --all && echo "✅ call-task: 已拉取最新代码") &

# 服务 2
(cd ../tiktok-shop && git fetch --all && echo "✅ tiktok-shop: 已拉取最新代码") &

# 服务 3
(cd ../constants && git fetch --all && echo "✅ constants: 已拉取最新代码") &

# 等待所有任务完成
wait
```

**重要说明**：
- ✅ 必须先定位服务目录（第零步），再执行 git 操作
- ✅ 必须在每个涉及的服务目录中执行 `git fetch --all`
- ✅ 确保对比的是最新的远程分支状态
- ✅ 避免因本地分支过时导致的信息不准确
- ⚠️ 如果某个服务拉取失败（如网络问题），记录错误但继续处理其他服务

### 第二步：收集 Git 信息

**对每个服务**（来自第零步的服务映射表），依次收集以下信息：

```bash
# 进入服务目录
cd <服务实际路径>

# 1. 查找最新的 release 分支（重要！）
latest_release=$(git branch -r | grep "origin/release_20" | grep -E "release_[0-9]{8}$" | sort -V | tail -1 | sed 's/origin\///' | xargs)

# 2. 获取当前分支
current_branch=$(git branch --show-current)

# 3. 显示结果
echo "服务: <服务名>"
echo "  当前分支: $current_branch"
echo "  最新 release: $latest_release"
```

**并行执行优化**（可选）：

如果有多个服务，可以并行收集以节省时间：

```bash
# 定义收集函数
collect_git_info() {
    local service_name=$1
    local service_path=$2
    cd "$service_path"
    local latest_release=$(git branch -r | grep "origin/release_20" | grep -E "release_[0-9]{8}$" | sort -V | tail -1 | sed 's/origin\///' | xargs)
    local current_branch=$(git branch --show-current)
    echo "✅ $service_name: $current_branch → $latest_release"
}

# 并行执行
collect_git_info "call-task" "../call-task" &
collect_git_info "tiktok-shop" "../tiktok-shop" &
collect_git_info "constants" "../constants" &

# 等待所有任务完成
wait
```

**重要说明**：
- ✅ 必须先执行步骤 1 查找最新的 release 分支，不要使用固定的分支名
- ✅ 使用 `sort -V` 进行版本号排序，确保获取到最新的分支
- ✅ 对比时使用 `origin/[分支名]` 格式，确保对比远程分支
- ✅ **不需要收集提交记录和文件变更列表**，只需要分支信息即可
- ⚠️ 如果某个服务没有 release 分支，记录为 \"无 release 分支\" 并继续

**收集结果示例**：

```
服务 Git 信息：
┌─────────────┬──────────────────┬─────────────────────┐
│ 服务名      │ 当前分支         │ 最新 release 分支   │
├─────────────┼──────────────────┼─────────────────────┤
│ call-task   │ feature/add-mq   │ release_20260301    │
│ tiktok-shop │ feature/add-api  │ release_20260228    │
│ constants   │ feature/add-enum │ release_20260225    │
└─────────────┴──────────────────┴─────────────────────┘
```

### 第三步：扫描 SQL 变更

SQL 变更的识别采用**多源收集**策略，确保不遗漏任何数据库变更。

#### 方法 1：扫描 SQL 变更目录

扫描项目中的 SQL 变更目录（通常为 `doc/changelog/`），找到与当前分支功能相关的 SQL 文件：

```bash
# 进入服务目录
cd <服务实际路径>

# 查找 SQL 文件
find doc/changelog -name "*.sql" -type f 2>/dev/null

# 或者使用 Glob 工具
# 模式：doc/changelog/**/*.sql
```

**读取 SQL 文件内容**：
- 使用 Read 工具读取每个 SQL 文件的完整内容
- 记录文件路径和内容，用于生成文档

#### 方法 2：从 Git 提交记录中查找 SQL 文件

通过 git diff 查找本次变更中涉及的 SQL 文件：

```bash
# 进入服务目录
cd <服务实际路径>

# 查找最新的 release 分支
latest_release=$(git branch -r | grep "origin/release_20" | grep -E "release_[0-9]{8}$" | sort -V | tail -1 | sed 's/origin\///' | xargs)

# 对比当前分支与最新 release 分支，找出新增或修改的 SQL 文件
git diff --name-only origin/$latest_release...HEAD | grep -E "\.sql$"

# 查看这些 SQL 文件的具体变更
git diff origin/$latest_release...HEAD -- "*.sql"
```

**识别 SQL 文件的特征**：
- 文件扩展名为 `.sql`
- 通常位于 `doc/changelog/`、`sql/`、`db/migration/` 等目录
- 文件名可能包含日期或版本号（如 `20260301_add_user_table.sql`）

#### 方法 3：从实体类变更中推断 SQL

分析 Java 实体类（Entity）的变更，自动生成对应的 DDL 语句。

**步骤 1：识别实体类变更**

```bash
# 查找变更的实体类文件
git diff --name-only origin/$latest_release...HEAD | grep -E "entity|domain|model" | grep "\.java$"

# 或者更精确地查找带 @Entity 注解的类
git diff origin/$latest_release...HEAD | grep -B 5 "@Entity"
```

**步骤 2：分析实体类变更类型**

使用 Read 工具读取变更的实体类文件，分析变更类型：

**变更类型 A：新增实体类（新表）**

识别特征：
- 文件是新增的（git diff 显示为 `new file`）
- 类上有 `@Entity` 或 `@Table` 注解

生成 SQL：
```sql
-- 根据实体类字段生成 CREATE TABLE 语句
CREATE TABLE `table_name` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `field_name` varchar(255) DEFAULT NULL COMMENT '字段说明',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表说明';
```

**变更类型 B：实体类新增字段（新增列）**

识别特征：
- 文件是修改的（git diff 显示为 `modified`）
- 新增了带 `@Column` 注解的字段

生成 SQL：
```sql
-- 根据新增字段生成 ALTER TABLE 语句
ALTER TABLE `table_name`
ADD COLUMN `new_field` varchar(255) DEFAULT NULL COMMENT '字段说明' AFTER `existing_field`;
```

**变更类型 C：实体类修改字段（修改列）**

识别特征：
- 字段的类型、长度、注解发生变化

生成 SQL：
```sql
-- 根据字段变更生成 ALTER TABLE 语句
ALTER TABLE `table_name`
MODIFY COLUMN `field_name` varchar(500) DEFAULT NULL COMMENT '修改后的说明';
```

**步骤 3：字段类型映射规则**

Java 类型到 MySQL 类型的映射：

| Java 类型 | MySQL 类型 | 说明 |
|----------|-----------|------|
| `Long`, `long` | `bigint(20)` | 长整型 |
| `Integer`, `int` | `int(11)` | 整型 |
| `String` | `varchar(255)` | 字符串（默认长度 255） |
| `String` (带 `@Column(length=500)`) | `varchar(500)` | 字符串（指定长度） |
| `String` (带 `@Lob`) | `text` | 长文本 |
| `Date`, `LocalDateTime` | `datetime` | 日期时间 |
| `LocalDate` | `date` | 日期 |
| `Boolean`, `boolean` | `tinyint(1)` | 布尔值 |
| `BigDecimal` | `decimal(19,2)` | 精确小数 |
| `Enum` | `varchar(50)` | 枚举（存储枚举名） |

**步骤 4：提取注释信息**

从实体类中提取注释信息，用于生成 SQL 的 COMMENT：

```java
// 从 Javadoc 注释中提取
/**
 * 用户名
 */
private String username;

// 从 @Column 注解中提取
@Column(name = "username", columnDefinition = "varchar(100) COMMENT '用户名'")
private String username;

// 从 @ApiModelProperty 注解中提取（Swagger）
@ApiModelProperty("用户名")
private String username;
```

**步骤 5：生成完整的 DDL 语句**

综合以上信息，生成完整的 DDL 语句：

```sql
-- ============================================
-- 自动生成的 SQL（基于实体类变更）
-- 生成时间：2026-03-05
-- 服务：call-task
-- 实体类：com.example.entity.User
-- ============================================

-- 新增表：t_user
CREATE TABLE `t_user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username` varchar(100) NOT NULL COMMENT '用户名',
  `email` varchar(255) DEFAULT NULL COMMENT '邮箱',
  `status` tinyint(1) DEFAULT '1' COMMENT '状态：0-禁用，1-启用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 新增字段：t_order.remark
ALTER TABLE `t_order`
ADD COLUMN `remark` varchar(500) DEFAULT NULL COMMENT '备注' AFTER `status`;
```

#### 方法 4：综合判断

**优先级顺序**：
1. **优先使用方法 1**：如果 `doc/changelog/` 目录中有 SQL 文件，直接使用
2. **补充使用方法 2**：从 git 提交中查找其他位置的 SQL 文件
3. **兜底使用方法 3**：如果没有找到 SQL 文件，但有实体类变更，则自动生成 SQL

**输出格式**：

在发版文档中，分别标注 SQL 的来源：

```markdown
## SQL 变更

### 1. 手动编写的 SQL（来自 doc/changelog/）

**文件**：`doc/changelog/20260301_add_user_table.sql`

```sql
CREATE TABLE `t_user` (
  ...
);
```

### 2. 从实体类推断的 SQL（自动生成）

**实体类**：`com.example.entity.Order`
**变更类型**：新增字段

```sql
ALTER TABLE `t_order`
ADD COLUMN `remark` varchar(500) DEFAULT NULL COMMENT '备注' AFTER `status`;
```

**重要提示**：
- ⚠️ 自动生成的 SQL 仅供参考，请在执行前仔细检查
- ⚠️ 索引、外键、分区等高级特性需要手动补充
- ⚠️ 建议在测试环境验证后再应用到生产环境
```

**如果没有 SQL 变更**：
- 方法 1、2、3 都没有找到 SQL 相关变更
- 在文档中明确标注"本次发版无 SQL 变更"

### 第四步：分析跨服务依赖

如果用户提到了多个项目目录（如 call-task、constants 等关联项目），对每个项目同样收集 git 信息和变更内容，并分析服务间的依赖关系以确定发版顺序。

依赖分析原则：
- 基础库/常量包（如 constants）最先发布
- SDK 包其次
- 中间层服务（如 call-task）再次
- 上层应用服务（如 tiktok-shop）最后

### 第五步：分析配置变更

扫描代码变更，识别是否需要以下配置初始化：

| 检查项 | 识别方式 |
|--------|----------|
| MQ Topic | 搜索 `@ClusteringMessageListener`、`@BroadcastMessageListener` 等注解中的新 topic |
| Nacos 配置 | 搜索新增的 `@Value` 或 `@ConfigurationProperties` |
| XXL-JOB 任务 | 搜索新增的 `@XxlJob` 注解 |
| Redis Key | 搜索新增的 Redis key 常量 |
| 数据库表 | 从 SQL 脚本中识别 CREATE TABLE / ALTER TABLE |
| 其他配置 | SDK版本、第三方服务配置、环境变量等 |

### 第六步：触发代码审核

在生成最终文档之前，先触发代码审核技能对本次变更进行审核：

```
使用 Skill 工具调用 requesting-code-review 技能
```

**审核内容**：
- 代码质量检查
- 潜在问题识别
- 最佳实践建议
- 安全性审查

**审核结果处理**：
- 记录审核中发现的问题和建议
- 将重要的审核发现纳入发版文档的"代码审核结果"章节

### 第七步：分析是否需要压测

根据代码变更内容，判断是否需要进行压测：

**需要压测的场景**：
- 修改了核心业务接口的查询逻辑
- 新增了高并发场景的接口
- 修改了缓存策略或数据库索引
- 新增了批量处理逻辑
- 修改了 MQ 消费逻辑
- 修改了定时任务的执行逻辑（涉及大量数据处理）

**无需压测的场景**：
- 仅新增字段，不影响查询性能
- 修复小 bug，不涉及性能相关代码
- 仅修改配置项或常量
- 仅新增管理后台功能（低并发场景）

**压测建议输出**：
- 明确标注"需要"或"不需要"压测
- 说明判断依据
- 如需压测，提供压测方案建议（目标 QPS、响应时间、压测接口等）

### 第八步：生成最终文档

根据前面收集的信息和代码审核结果，按照 `references/release_doc_template.md` 中的模板格式生成发版文档，输出到当前需求目录的根目录下。

文件命名规则：`发版文档_[功能简述].md`

**文档应包含**：
- 基本信息、涉及服务、发版顺序
- SQL 变更、配置初始化
- **代码审核发现的问题和建议**（如有）
- 验证方案、回滚方案

## 注意事项

- 所有表格使用 markdown 格式
- SQL 脚本需完整展示，不要省略；如无 SQL 变更需明确标注
- 发版顺序必须明确标注依赖关系
- 验证方案要具体，包含 SQL 语句、日志关键字、API 路径等可执行的验证步骤
- 回滚方案要考虑数据兼容性（新增字段通常无需回滚SQL）
- 代码审核结果要如实记录，重要问题需在文档中突出显示
- **不要在文档中展示提交记录和文件变更列表**，只需要变更说明即可
- 文档语言为中文

### SQL 推断相关注意事项（重要）

#### 1. 自动生成 SQL 的局限性

**⚠️ 以下场景需要人工补充**：

- **索引策略**：自动生成的索引可能不符合实际查询场景
  - 示例：只生成了 `idx_user_id`，但实际需要 `idx_user_id_create_time` 联合索引
  - 建议：根据实际查询语句补充索引

- **外键约束**：自动生成不包含外键定义
  - 示例：`user_id` 字段应该关联 `t_user.id`
  - 建议：根据业务关系手动添加外键

- **分区表**：自动生成不支持分区策略
  - 示例：日志表需要按月分区
  - 建议：手动添加分区定义

- **默认值**：可能无法准确推断业务默认值
  - 示例：`status` 字段默认值应该是 `1`（启用），而不是 `NULL`
  - 建议：检查并修正默认值

- **字段顺序**：新增字段的位置可能不合理
  - 示例：`AFTER` 子句指定的位置可能不是最佳位置
  - 建议：根据表结构调整字段顺序

#### 2. 实体类注解识别规则

**支持的注解**：
- `@Entity`：标识实体类
- `@Table(name = "table_name")`：指定表名
- `@Column(name = "column_name", length = 100, nullable = false)`：指定列属性
- `@Id`：标识主键
- `@GeneratedValue`：标识自增主键
- `@Lob`：标识大字段（TEXT/BLOB）
- `@Temporal`：标识日期时间类型

**不支持的注解**（需要手动处理）：
- `@Index`：索引定义（JPA 2.1+）
- `@UniqueConstraint`：唯一约束
- `@ForeignKey`：外键约束
- 自定义注解（如 `@Sharding`、`@Partition` 等）

#### 3. 字段类型推断的特殊情况

**枚举类型**：
```java
@Enumerated(EnumType.STRING)
private StatusEnum status;
```
- 推断为 `varchar(50)`
- 建议：根据枚举值长度调整字段长度

**JSON 字段**：
```java
@Column(columnDefinition = "json")
private String config;
```
- 推断为 `json` 类型（MySQL 5.7+）
- 建议：确认数据库版本支持 JSON 类型

**大字段**：
```java
@Lob
private String content;
```
- 推断为 `text` 或 `longtext`
- 建议：根据内容大小选择合适的类型（`text` vs `mediumtext` vs `longtext`）

#### 4. 表名和字段名映射规则

**驼峰转下划线**：
- Java：`userName` → MySQL：`user_name`
- Java：`createTime` → MySQL：`create_time`

**表名前缀**：
- 如果实体类没有 `@Table` 注解，默认使用类名转下划线
- 示例：`UserLog` → `user_log`
- 建议：检查是否需要添加表名前缀（如 `t_user_log`）

#### 5. 验证和测试建议

**在测试环境验证**：
1. 先在测试环境执行自动生成的 SQL
2. 检查表结构是否符合预期
3. 运行应用程序，验证 ORM 映射是否正确
4. 执行相关的单元测试和集成测试

**对比工具验证**：
- 使用 Flyway、Liquibase 等工具对比表结构差异
- 使用 `SHOW CREATE TABLE` 对比生产环境和测试环境的表结构

**性能测试**：
- 对于新增的索引，使用 `EXPLAIN` 分析查询计划
- 对于大表的 ALTER TABLE 操作，评估锁表时间和影响范围

#### 6. 文档中的标注规范

**明确标注 SQL 来源**：
```markdown
### 手动编写的 SQL
**文件**：`doc/changelog/20260301_xxx.sql`
✅ 已人工审核

### 从实体类推断的 SQL（自动生成）
**实体类**：`com.example.entity.User`
⚠️ 自动生成，需要人工审核
```

**标注风险等级**：
- 🟢 低风险：新增字段（允许 NULL）
- 🟡 中风险：新增字段（NOT NULL，有默认值）
- 🔴 高风险：修改字段类型、删除字段、大表 ALTER TABLE

**提供回滚方案**：
- 新增表：`DROP TABLE IF EXISTS table_name;`
- 新增字段：`ALTER TABLE table_name DROP COLUMN column_name;`
- 修改字段：提供修改前的字段定义

### 验证方案编写原则（重要）

**不要假设数据库表的存在**：
- 只基于实际的 SQL 变更脚本和代码中的实体类来编写数据库验证
- 不要凭空假设存在 MQ 消费日志表、操作日志表等
- 如果需要验证 MQ 消费、异步任务等，优先使用应用日志验证
- 数据库验证仅限于：
  1. 本次 SQL 脚本中涉及的表和字段
  2. 代码中明确操作的表（通过 Entity、Mapper 确认）

**验证方案示例**：
- ✅ 正确：通过应用日志验证 MQ 消费（搜索日志关键字）
- ✅ 正确：查询本次 SQL 脚本中新增/修改的表和字段
- ❌ 错误：假设存在 t_mq_consume_log 表并编写查询语句
- ❌ 错误：假设存在操作日志表记录业务操作

## 使用示例

### 示例 1：多服务发版文档

**用户输入**：
```
写发版文档，这次改动涉及 tiktok-shop、call-task、constants 三个项目
```

**Skill 执行流程**：

**第零步：定位服务目录**
1. 解析用户输入，识别出 3 个服务：tiktok-shop、call-task、constants
2. 在父目录中查找这些服务：
   ```bash
   ls -d ../tiktok-shop ../call-task ../constants
   ```
3. 验证每个目录是否为 git 仓库
4. 记录服务映射表：
   ```
   - tiktok-shop → C:\workspace\tiktok-shop
   - call-task → C:\workspace\call-task
   - constants → C:\workspace\constants
   ```

**第一步：拉取最新代码**
```bash
(cd ../tiktok-shop && git fetch --all) &
(cd ../call-task && git fetch --all) &
(cd ../constants && git fetch --all) &
wait
```

**第二步：收集 Git 信息**
```bash
# 对每个服务执行
cd ../tiktok-shop && git branch --show-current
cd ../call-task && git branch --show-current
cd ../constants && git branch --show-current
```

**第三步：扫描 SQL 变更**
- 在 tiktok-shop 的 `doc/changelog/` 目录找到相关 SQL 文件
- 读取完整内容

**第四步：分析依赖关系**
- 识别依赖顺序：constants → call-task → tiktok-shop

**第五步：分析配置变更**
- 搜索 `@ClusteringMessageListener`、`@XxlJob` 等注解

**第六步：触发代码审核**
- 调用 `requesting-code-review` 技能

**第七步：分析是否需要压测**
- 根据代码变更判断

**第八步：生成文档**
- 输出到 `tiktok-shop/doc/发版文档_[功能名].md`

**生成的文档包含**：
- 基本信息（需求、日期、开发者）
- 三个服务的分支信息
- 发版顺序（constants → call-task → tiktok-shop）
- SQL 变更脚本（完整内容）
- 初始化配置（MQ/Nacos/XXL-JOB/Redis/其他）
- 代码审核发现的问题和建议
- 验证方案（具体的 SQL、日志关键字、API）
- 回滚方案

---

### 示例 2：单服务发版文档（当前目录）

**用户输入**：
```
写发版文档
```

**Skill 执行流程**：

**第零步：定位服务目录**
1. 用户未指定服务，默认为当前目录
2. 获取当前目录名：
   ```bash
   basename $(pwd)
   # 输出：call-task
   ```
3. 验证是否为 git 仓库
4. 记录服务映射表：
   ```
   - call-task → C:\workspace\call-task（当前目录）
   ```

**后续步骤**：
- 与示例 1 相同，但只处理单个服务

---

### 示例 3：服务名不完全匹配

**用户输入**：
```
写发版文档，涉及 company-server 和 ai-quartz
```

**Skill 执行流程**：

**第零步：定位服务目录**
1. 解析用户输入，识别出 2 个服务：company-server、ai-quartz
2. 尝试精确匹配，未找到
3. 使用模糊匹配：
   ```bash
   find .. -maxdepth 2 -type d -iname "*company*"
   # 找到：../company

   find .. -maxdepth 2 -type d -iname "*quartz*"
   # 找到：../ai-service/quartz
   ```
4. 使用 AskUserQuestion 确认：
   ```json
   {
     "questions": [{
       "question": "找到以下可能的服务目录，请确认",
       "header": "服务确认",
       "multiSelect": false,
       "options": [
         {"label": "company-server → ../company", "description": "公司服务"},
         {"label": "ai-quartz → ../ai-service/quartz", "description": "AI 定时任务服务（子模块）"}
       ]
     }]
   }
   ```
5. 用户确认后，记录服务映射表

**后续步骤**：
- 与示例 1 相同

---

### 示例 5：从实体类推断 SQL

**用户输入**：
```
写发版文档
```

**场景**：
- 当前服务：call-task
- 没有手动编写的 SQL 文件
- 但有实体类变更

**Skill 执行流程**：

**第三步：扫描 SQL 变更**

1. **方法 1**：扫描 `doc/changelog/` 目录
   ```bash
   find doc/changelog -name "*.sql" -type f
   # 结果：未找到 SQL 文件
   ```

2. **方法 2**：从 git 提交中查找 SQL 文件
   ```bash
   git diff --name-only origin/release_20260228...HEAD | grep -E "\.sql$"
   # 结果：未找到 SQL 文件
   ```

3. **方法 3**：从实体类变更中推断 SQL
   ```bash
   # 查找变更的实体类
   git diff --name-only origin/release_20260228...HEAD | grep -E "entity|domain" | grep "\.java$"
   # 结果：
   # - src/main/java/com/example/entity/Order.java (modified)
   # - src/main/java/com/example/entity/UserLog.java (new file)
   ```

4. **分析实体类变更**

   **变更 A：Order.java（修改）**
   ```bash
   git diff origin/release_20260228...HEAD -- src/main/java/com/example/entity/Order.java
   ```

   发现新增字段：
   ```java
   /**
    * 备注
    */
   @Column(name = "remark", length = 500)
   private String remark;
   ```

   **生成 SQL**：
   ```sql
   -- 新增字段：t_order.remark
   ALTER TABLE `t_order`
   ADD COLUMN `remark` varchar(500) DEFAULT NULL COMMENT '备注' AFTER `status`;
   ```

   **变更 B：UserLog.java（新增）**
   ```bash
   git show HEAD:src/main/java/com/example/entity/UserLog.java
   ```

   发现新增实体类：
   ```java
   @Entity
   @Table(name = "t_user_log")
   public class UserLog {
       @Id
       @GeneratedValue(strategy = GenerationType.IDENTITY)
       private Long id;

       @Column(name = "user_id", nullable = false)
       private Long userId;

       @Column(name = "action", length = 100)
       private String action;

       @Column(name = "create_time")
       private LocalDateTime createTime;
   }
   ```

   **生成 SQL**：
   ```sql
   -- 新增表：t_user_log
   CREATE TABLE `t_user_log` (
     `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
     `user_id` bigint(20) NOT NULL COMMENT '用户ID',
     `action` varchar(100) DEFAULT NULL COMMENT '操作',
     `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
     PRIMARY KEY (`id`),
     KEY `idx_user_id` (`user_id`)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户日志表';
   ```

**生成的文档包含**：

```markdown
## SQL 变更

### 从实体类推断的 SQL（自动生成）

#### 1. 新增表：t_user_log

**实体类**：`com.example.entity.UserLog`
**变更类型**：新增实体类

```sql
CREATE TABLE `t_user_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `action` varchar(100) DEFAULT NULL COMMENT '操作',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户日志表';
```

#### 2. 新增字段：t_order.remark

**实体类**：`com.example.entity.Order`
**变更类型**：新增字段

```sql
ALTER TABLE `t_order`
ADD COLUMN `remark` varchar(500) DEFAULT NULL COMMENT '备注' AFTER `status`;
```

**重要提示**：
- ⚠️ 以上 SQL 为自动生成，仅供参考
- ⚠️ 请在测试环境验证后再应用到生产环境
- ⚠️ 索引策略需要根据实际查询场景调整
```

---

### 示例 6：混合 SQL 来源

**用户输入**：
```
写发版文档，涉及 call-task 和 constants
```

**场景**：
- call-task：有手动编写的 SQL 文件
- constants：没有 SQL 文件，但有实体类变更

**生成的文档包含**：

```markdown
## SQL 变更

### 服务：call-task

#### 手动编写的 SQL

**文件**：`doc/changelog/20260301_add_mq_config.sql`

```sql
CREATE TABLE `t_mq_config` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `topic` varchar(100) NOT NULL,
  `tag` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 服务：constants

#### 从实体类推断的 SQL（自动生成）

**实体类**：`com.example.constants.entity.ConfigItem`
**变更类型**：新增字段

```sql
ALTER TABLE `t_config_item`
ADD COLUMN `category` varchar(50) DEFAULT NULL COMMENT '配置分类' AFTER `name`;
```

**重要提示**：
- ⚠️ constants 服务的 SQL 为自动生成，请在执行前仔细检查
```

**用户输入**：
```
写发版文档，涉及 unknown-service
```

**Skill 执行流程**：

**第零步：定位服务目录**
1. 解析用户输入，识别出 1 个服务：unknown-service
2. 尝试所有查找方法，均未找到
3. 使用 AskUserQuestion 询问用户：
   ```json
   {
     "questions": [{
       "question": "未找到服务 'unknown-service'，请选择操作",
       "header": "服务未找到",
       "multiSelect": false,
       "options": [
         {"label": "提供完整路径", "description": "手动输入服务的完整路径"},
         {"label": "跳过该服务", "description": "继续处理其他服务"},
         {"label": "取消操作", "description": "停止生成发版文档"}
       ]
     }]
   }
   ```
4. 根据用户选择处理

**后续步骤**：
- 如果用户提供路径，验证后继续
- 如果用户跳过，处理其他服务
- 如果用户取消，停止流程
