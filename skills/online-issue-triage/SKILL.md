---
name: online-issue-triage
description: 94AI 线上问题排查方法论。覆盖三大场景: 1) 技术 trace 排查 (NPE/异常/慢调用) 2) 号码为什么没导入任务 3) 号码在智能任务为什么没流转。按场景串联 SLS 日志查询 (aliyun-sls-log-query)、本地代码定位 (D:\Code)、Archery 数据库查询 (archery-prod-query) 三个工具。当用户问"这个 trace 是什么报错"、"号码为什么没导入进去"、"号码在智能任务为什么没流转"、"运营反馈号码没收到短信"、"批量号码没成功"等线上问题时使用本技能。
---

# 线上问题排查方法论

## 总框架

任何线上问题, 排查路径都是 **现象 → 日志 → 代码 → 数据** 四步走, 三个工具各管一段:

| 阶段 | 工具 / Skill | 拿到什么 |
|------|--------------|----------|
| **现象** | 用户输入 + 业务表查询 | 关键 ID (trace/号码/smsId/taskId/flowDataId) 和现象描述 |
| **日志 (SLS)** | `aliyun-sls-log-query` | 发生了什么、抛了什么异常、完整调用链 |
| **代码** | 在 `D:\Code` 直接读 | 异常为什么会抛、命中的判断分支 |
| **数据 (Archery)** | `archery-prod-query` | 业务对象当前状态, 验证假设 |

**核心原则**:
- **技术问题** (给 trace ID): 先 SLS → 再代码 → 再 Archery 验证
- **业务问题** (号码/任务/订单): 先 Archery 看状态 → 再 SLS 反查时间点 → 再代码定位

## 最常见入口: 号码 + 任务 ID (80% 的情况)

线上排查绝大多数情况**只给一个号码 + 一个任务 ID**, 没有 trace ID。直接按下面路径走:

### Step 1: 明确两个 ID 的含义

| ID | 可能的形态 | 对应的表 / 字段 |
|----|------------|-----------------|
| **号码** | 明文手机号 (如 `13800138000`) / numberId (资源 ID) / 加密后 (MD5/SHA) | `ai_number`, `ai_task_detail.number`, `ai_sms.number` |
| **任务 ID** | 智能外呼任务 / 群发任务 / 流程任务 / call_task / flowDataId | `ai_task`, `call_task`, `ai_task_detail`, `flow_data` |

**注意**:
- 用户给的"任务 ID"可能是 `taskId` 也可能是 `flowDataId` / `requestId` / `flowTaskNodeDataId`, 先问清楚或通过下面 Archery 查证
- 号码在系统里可能存的是 MD5 (看 `ai_task_detail.number` 是否 32 hex), 不要直接用明文搜
- 海外号码可能带 country code (`+86xxx` / `86xxx`), 注意格式归一化

### Step 2: Archery 三连查 (国内 / 海外库分开, 先确认号码归属)

```sql
-- 1. 任务基本信息 (确认任务存在, 看 status / type / company_id)
SELECT * FROM ai_task WHERE id = <taskId>;

-- 2. 这个号码在该任务下的状态 (关键! 看是否真的没导入/没流转)
SELECT * FROM ai_task_detail
WHERE task_id = <taskId>
  AND (number = '<明文>' OR number = '<MD5>' OR number_id = <numberId>);

-- 3. 如果是流程任务, 看流程实例状态
SELECT * FROM flow_data
WHERE task_id = <taskId> AND (number = '<号码相关字段>' OR ...);
```

通过这三条拿到:
- **号码到底在不在任务里** (区分"没导入" vs "导入了但没流转")
- **当前 status / error_status** 字段 (直接告诉失败原因)
- **关联的 flowDataId / requestId / smsId** (后续排查的钥匙)
- **创建时间 / 最后更新时间** (SLS 反查的时间窗口)

### Step 3: 从业务对象反查 trace ID (可选)

如果业务表里有 `trace_id` 字段 (不同业务不一定有), 直接拿; 没有 trace ID **不影响排查**, SLS 也能用业务关键词查。

### Step 4: SLS 反查时间窗口

用 Step 2 拿到的时间 + 业务 ID 当关键词:

```bash
# 用号码 + taskId 当关键词
python .../aliyun_sls_query.py --query '"13800138000" and "12345" and ERROR' --minutes 60

# 用 flowDataId / smsId 反查
python .../aliyun_sls_query.py --query '<flowDataId>' --minutes 60

# 时间窗口精确 (推荐)
python .../aliyun_sls_query.py --from <创建时间-5min> --to <创建时间+15min> \
    --query '"13800138000" and "<taskId>"'
```

**关键**: 先选对 project (国内 / 海外 / Open API), 看 `ai_task` 表里的 `company_id` 或任务的部署区。

### Step 5: 代码定位拦截点 / 异常分支

根据 SLS 里看到的 ERROR 栈帧或拦截日志, 在 `D:\Code` 对应工程里定位代码 (按"场景 1"的代码定位步骤)。

### 号码 + 任务 ID 排查的常见结论

| 现象 | 可能原因 | 验证方法 |
|------|----------|----------|
| `ai_task_detail` 里查不到这个号码 | 号码根本没导入 | 看导入批次日志 / 文件解析 |
| `ai_task_detail.status` = 拦截码 | 黑名单 / 去重 / 容量上限 | 对应黑名单表 / 配置 |
| `ai_task_detail` 存在但 `flow_data` 没有 | 没触发流程 / 触发条件不满足 | 看流程触发器日志 |
| `flow_data.status` = ERROR / 异常退出 | 流程中某节点抛异常 | 看 ai-flow-server 日志, 找异常栈 |
| 数据完全正常但没生效 | 缓存 / MQ 没消费 | 看 RocketMQ 死信 + Redis 缓存 |

## 三大典型场景

### 场景 1: 技术 trace 排查

**触发**: 用户给一个 trace ID (16 hex 字符) 问 "这是什么报错"

**步骤**:

1. **SLS 查日志** (用 `aliyun-sls-log-query`)
   - 默认国内 project, 0 条 → 切海外 → 再不行切 Open API
   - 命令: `--trace-id <id> --minutes 60 --size 50 --full --out trace.json`
   - 找 ERROR / Exception / 关键栈帧 file:line

2. **代码定位** (在 `D:\Code`)
   - 用 Glob/Grep, **不要用 find/grep** (目录太大, 全量搜超时)
   - 缩小到具体工程目录再搜
   - 常见服务 → 工程目录映射:

   | 服务 | 工程目录 |
   |------|----------|
   | sms-consumer | `D:\Code\sms\consumer` |
   | sms-api / sms-server | `D:\Code\sms-api` / `D:\Code\sms-server` |
   | ai-flow-server | `D:\Code\ai-flow` |
   | data-center | `D:\Code\data-center` |
   | call-task | `D:\Code\call-task` |
   | agentcc | `D:\Code\agentcc` |
   | ai-admin | `D:\Code\ai` (或 `ai-admin-ui`) |

   - 找 NPE / 空值 / 越界 / 未覆盖分支点

3. **Archery 验证假设** (用 `archery-prod-query`)
   - 查业务表里实际数据状态
   - 验证嫌疑分支是否真的命中
   - 国内 / 海外实例分开, 注意选对

4. **综合日志 + 代码 + 数据, 给结论 + 修复建议**

**实例参考** (trace `fe650d50a6be0dae`):
- 海外 SLS 查到 sms-consumer 抛 NPE, 栈到 `SmsReportService.handleHangupStatusReport`
- 代码定位 `SmsReportService.buildSmsStatusEvent:3000-3003`, `smsExtend.getSendPlanGroupId()` 没判空
- Archery 查 `ai_sms` (smsId=374318962) 看 `interaction_type` / `send_type` / `remark` 验证

### 场景 2: 号码为什么没导入

**触发**: 运营反馈 "号码 X 没导入到任务 Y / 没进系统"

**通用步骤**: 按上面"最常见入口"章节 Step 1-5 走。本场景重点关注:

**Archery 判断 (在通用 Step 2 之后)**:

查 `ai_task_detail` 是否有这个号码 → 直接区分两种情况:

| `ai_task_detail` 查询结果 | 结论 | 下一步 |
|---------------------------|------|--------|
| **查不到** | 号码根本没导入成功 | 找导入批次记录 / 文件解析日志 (SLS 关键词: `import` + taskId + 号码) |
| **能查到, `status` = 拦截码** | 导入了但被拦截 | 按拦截码查对应配置 (黑名单/去重/容量) |
| **能查到, status 正常** | 导入成功了但运营以为没成功 | 看 ai_task_detail 的 number 字段是否被 MD5 (运营用明文搜会搜不到) |

**导入拦截常见原因** (代码侧定位):

- 黑名单 (`ai_blacklist`): call-task / data-center 通常有 BlackListFilter 类
- 重复 (unique 约束 / 业务去重): `ai_task_detail` 有 unique 索引或前置去重 SQL
- 号码格式校验失败: 正则在导入入口 Service 里
- 任务容量上限: 任务配置或公司配额
- companyId / 用户权限不足: Auth 校验

**SLS 关键词** (海外号码切海外 project):
```
"<number>" and "<taskId>" and (ERROR or WARN or "拦截" or "duplicate")
"<taskId>" and "import"
```

### 场景 3: 号码在智能任务为什么没流转

**触发**: 号码进了任务但没流转到下一节点 (典型: 智能外呼、流程节点卡住)

**通用步骤**: 按上面"最常见入口"章节 Step 1-5 走。本场景重点关注:

**Archery 判断 (在通用 Step 2 之后)**:

```sql
-- 1. 看流程实例
SELECT flow_data_id, status, error_status, current_node, create_time, alter_time
FROM flow_data WHERE task_id = <taskId> AND <number 条件>;

-- 2. 看节点数据 (按 flowDataId 关联)
SELECT flow_task_node_data_id, flow_data_id, status, error_status, request_id, alter_time
FROM flow_task_node_data
WHERE flow_data_id IN (<上一步拿到的 flowDataId>);

-- 3. 如果有 requestId, 反查这个 requestId 的状态
SELECT * FROM flow_task_node_data WHERE request_id = <requestId>;
```

**异常类型 → 根因对照表** (SLS 里看到什么就对照):

| 异常 / 现象 | 根因 | 排查方向 |
|-------------|------|----------|
| `DataInconsistencyException: 存在等待执行的节点` | 上游节点未完成 / 锁未释放 | Archery 查异常里的 `requestId` 状态, 看是卡住还是被占用 |
| `AppBusinessException` | 业务校验失败 (前置条件不满足) | 看异常 message, 反查代码 |
| `CannotAcquireLockException` / lock timeout | 锁竞争 | 看是否同号被并发触发 |
| `flow_data.status` = ERROR | 流程中某节点抛异常退出 | 看对应 flow_task_node_data 的 error_status |
| 数据正常但实际没动 | 缓存 / MQ 死信 | 看 RocketMQ 死信队列 + Redis 流程缓存 |

**代码定位关键类** (工程目录 `D:\Code\ai-flow`):
- `ConditionDiverterFlowListener` — 条件分流入口
- `BaseFlowListener.preExecute` — 前置校验
- `DbConsistencyChecker.checkAndGetExecutingData` — 一致性检查 (DataInconsistencyException 抛出点)
- `LockTemplate.execute` — 锁模板


**实例参考** (trace `26f8600911293fe6`):
- ai-flow-server 抛 `DataInconsistencyException: 存在等待执行的节点, requestId=2459204585722880`
- 代码定位 `DbConsistencyChecker.checkAndGetExecutingData:37` ← `BaseFlowListener.preExecute:115`
- Archery 查 `flow_task_node_data` (requestId=2459204585722880) 当前状态, 看它为什么处于"等待执行"

## 关键原则

1. **SLS 多 project 切换是第一反应**
   - 国内默认 → 海外 → Open API
   - 查到 0 条日志时, **先怀疑 project 不对**, 再怀疑 trace 不存在

2. **国内 / 海外分库**
   - Archery 分国内 / 海外实例
   - 业务区分: 号码归属决定查哪个库; 短信看 sms-consumer 部署区
   - 海外典型服务: `sms-consumer`, 海外区 `ai-flow-server`, 海外 `call-task`

3. **代码搜索缩小路径**
   - `D:\Code` 全量 Glob/Grep 会超时
   - 先按服务名定位工程目录, 再在该目录下 Glob/Grep

4. **跨工具一致性校验**
   - 同一个 ID (smsId / flowDataId / requestId) 在 SLS 日志、Archery 数据里应该能对上
   - 时间戳对齐: SLS 用 Unix 秒, Archery 用 datetime, 注意时区 (国内 +8, 海外看具体地区)

5. **死信 / 重试追踪**
   - RocketMQ 消费失败默认会重试 N 次后进死信队列
   - 同一 msgId 多次出现 → 看是第几次重试, 业务代码要做幂等

## 常见服务 → SLS project 映射

| 服务 | 默认 SLS project |
|------|------------------|
| `data-center`, `ai-admin`, `ai-flow-server` (国内), `agentcc`, `call-task` (国内) | 国内 `k8s-log-c4128cc88f92f4757a78daa9f542b2446` |
| `sms-consumer`, `ai-flow-server` (海外), `call-task` (海外) | 海外 `k8s-log-cd49222ac975346ad967c81f92a4a1c82` |
| Open API 接入 | `94ai-all` (region=cn-shenzhen) |

## 常见表名速查 (参考, 以代码实际查询为准)

> 表名以代码里 DAO/Mapper 实际查询的为准, 这里只是排查时的脑图入口

| 场景 | 关键表 |
|------|--------|
| 短信 | `ai_sms`, `ai_sms_extend`, `ai_sms_template`, `ai_sms_short_url_relation` |
| 流程 | `flow_data`, `flow_task_node_data`, `flow_task_node` |
| 号码 | `ai_number`, `ai_blacklist`, `ai_task_detail` |
| 任务 | `ai_task`, `ai_task_detail`, `call_task` |
| 公司 | `ai_company`, `ai_company_user` |

## 输出规范

排查结论建议包含:

1. **根因** (一句话讲清楚)
2. **链路时间线** (表格, 按时间正序)
3. **关键信息** (应用、Pod、MQ topic、业务 ID、异常类型)
4. **代码位置** (`file:line`)
5. **业务影响** (这条失败影响什么、会不会重试、是否死信)
6. **修复 / 排查建议** (要不要查 DB 验证、要不要看相关 trace、要不要发版修代码)
