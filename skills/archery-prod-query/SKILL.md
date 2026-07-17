---
name: archery-prod-query
description: 通过 Archery 查 94AI 生产 MySQL, 只读安全工作流, 自动登录刷新 session。凭证 + MFA 写在 ~/.archery-credentials.json, archery_login.py 启 Chrome 自动登录 + 抓 csrftoken/sessionid 写到 ~/.archery_session.json, archery_query.py 直接用 session 发请求。覆盖场景: 列实例/库/表、读 ai_task / stat_day_base / t_smart_task 等业务表、拆分国内/海外口径、定位权限缺失。
---

# Archery Production Query

Use this skill whenever the next useful step is to pull **production read-only facts** through Archery rather than guessing from code or using direct database credentials.

Prefer the bundled script for repeatable queries. Keep queries read-only and keep the final write-up focused on the user's business ownership boundary instead of platform-wide vanity totals.

## 凭证 & Session 文件

凭证文件 (不进 git, 已配好): `C:\Users\54542\.archery-credentials.json`

```json
{
  "username": "lianwukun",
  "password": "xxx",
  "mfa_secret": "BASE32_TOTP_SEED",
  "base_url": "https://archery-k8s.94ai.pro",
  "login_path": "/login/",
  "target_url": "https://archery-k8s.94ai.pro/sqlquery/"
}
```

Session 文件 (由 archery_login.py 自动生成): `C:\Users\54542\.archery_session.json`

```json
{
  "base_url": "https://archery-k8s.94ai.pro",
  "csrf_token": "...",
  "cookie": "csrftoken=...; sessionid=...; ...",
  "cookies_dict": {"csrftoken": "...", "sessionid": "...", ...},
  "user_agent": "...",
  "url": "https://archery-k8s.94ai.pro/sqlquery/",
  "saved_at": 1750000000.0
}
```

依赖: `pip install selenium webdriver-manager pyotp requests` (首次需要)

Fallback: 如果没有 session 文件, `archery_query.py` 会回退到环境变量 `ARCHERY_BASE_URL` / `ARCHERY_CSRF_TOKEN` / `ARCHERY_COOKIE` (进程 → HKCU → HKLM)。**推荐用 session 文件**, 不用手动从浏览器复制 cookie。

## 工作流

### Step 1: 确认 session 是否还有效

```bash
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_query.py list-instances
```

- 拿到实例列表 → session 有效, 跳到 Step 3
- 报 401/403/302 或重定向到登录页 → session 过期, 走 Step 2
- 找不到 `~/.archery_session.json` → 首次使用, 走 Step 2

### Step 2: 登录刷新 session (约 30 秒)

```bash
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_login.py
```

脚本会:
1. 启 Chrome, 访问 `https://archery-k8s.94ai.pro/login/`
2. 自动填账号/密码, 自动填 TOTP 6 位 MFA (`pyotp.TOTP(secret).now()`)
3. 等待跳到主页 `/sqlquery/`
4. 抓 cookies (csrftoken + sessionid) 写到 `~/.archery_session.json`

### Step 3: 查数据

实例 / 库 / 表 / SQL 四级 API 都在 `archery_query.py`:

```powershell
# 列可读实例
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_query.py list-instances

# 列某实例下数据库
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_query.py `
  list-databases --instance "main-db"

# 列表
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_query.py `
  list-tables --instance "main-db" --database "ai_admin"

# 查列结构
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_query.py `
  query --instance "log-db" --database "auto_dialer_data" `
  --table "stat_day_base" --sql "show columns from stat_day_base"

# 跑只读聚合 (JSON 输出)
python C:\Users\54542\.codex\skills\archery-prod-query\scripts\archery_query.py `
  query --instance "main-db" --database "ai" --table "ai_task" --format json `
  --sql "select count(distinct flow_id) as smart_flow_cnt from ai_task where create_time >= '2026-01-01' and create_time < '2026-07-01' and flow_id is not null"
```

## Workflow (业务侧)

1. Confirm the business question first.
   - Decide whether the user needs:
   - table discovery
   - schema inspection
   - one-off counts
   - monthly trends
   - domestic vs overseas split
   - module-specific attribution such as new smart tasks, TikTok Shop outbound, AgentCC
2. Discover readable scope before writing SQL.
   - List readable instances first.
   - Then list databases for the chosen instance.
   - If needed, list tables for the chosen database.
3. Keep SQL read-only.
   - Use `select`, `show`, `desc`, `describe`, and metadata queries only.
   - Never run `insert`, `update`, `delete`, `alter`, `drop`, `truncate`, or DDL through this skill.
4. Separate platform background from personal attribution.
   - Do not write full-platform totals as the user's personal output unless the user explicitly owns that whole platform.
   - Prefer module-scoped data such as:
   - `ai.ai_task` with `flow_id is not null` for new smart-task subtasks
   - `count(distinct flow_id)` for deduplicated smart-task flow count
   - `stat_day_base` only when the business confirms its scope
   - business-side mapping tables, such as TikTok Shop `t_shop_task.task_id`, when splitting module-specific metrics
5. Report permission gaps clearly.
   - If Archery returns `Access denied`, stop guessing.
   - Tell the user exactly which instance, database, and table permission is missing.

## Common Patterns

### New Smart Task

Use these definitions unless the user explicitly corrects them:

- `flow_id is not null` in `ai.ai_task` = new smart-task node outbound tasks
- New smart-task quantity must be aggregated by smart-task ID, not node task rows.
  - In the current `ai.ai_task` path, use `count(distinct flow_id)` as the new smart-task count.
  - Treat `flow_id` as the smart-task ID / flow dimension for report counts unless the user gives a newer mapping field.
  - Never use `count(*)` or `count(distinct task_id)` from `ai_task` as the new smart-task count.
- When reporting task counts, use smart-task dimension only:
  - `count(distinct flow_id)` = new smart-task count
  - `ai_task.task_id` is only a node outbound-task mapping key for fact-table aggregation, not the task-count metric
- If the user asks for monthly trend, group by `date_format(create_time, '%Y-%m')`
- For new smart-task outbound volume:
  1. collect the node `ai_task.task_id` rows whose smart-task ID is in scope
  2. aggregate `stat_day_base` by those node `task_id` values
  3. report the smart-task count separately as `count(distinct flow_id)`

### Legacy Smart Task

Use this path for old smart-task statistics:

- domestic task table: `auto-db.ai_task.t_smart_task`
- domestic branch table: `auto-db.ai_task.t_smart_task_branch`
- domestic fact table: `log-db.auto_dialer_data.stat_day_base`
- overseas task table: `overseas-production-db.ai_task.t_smart_task` when that is the user-facing alias, or the literal Archery instance name in the environment
- overseas branch table: `overseas-production-db.ai_task.t_smart_task_branch`
- overseas fact table: `overseas-production-db.auto_dialer_data.stat_day_base`

Preferred mapping:

1. count old smart tasks from `t_smart_task`
2. map branch rows with `t_smart_task_branch.task_id = t_smart_task.id`
3. map outbound task rows with `t_smart_task_branch.target_task_id = stat_day_base.task_id`
4. aggregate import and call metrics from `stat_day_base`

When reporting old smart-task business results, prefer:

- task count
- covered companies
- mapped outbound task count
- import volume
- call volume

Do not include answer count or AB count if the user explicitly asks to remove them.

### Domestic / Overseas Split

Use different instances and keep the wording explicit:

- Common domestic instances: `main-db`, `log-db`
- Common overseas instance: `overseas-production-db` if that is the user-facing alias, or the literal Archery instance name used in the environment

Do not merge domestic and overseas numbers unless the user explicitly asks for a combined total.

### TikTok Shop Outbound

Do not assume any `shop_*` field means TikTok Shop business volume.

Preferred approach:

1. Confirm with the user whether TikTok Shop outbound results land in `stat_day_base`
2. Map TikTok Shop task tables to `stat_day_base.task_id`
3. Aggregate only those mapped tasks

Known useful mapping path:

- `polardb-tidb.tiktok_shop.t_shop_task.task_id` -> `stat_day_base.task_id`

Known TikTok Shop location:

- instance: `polardb-tidb`
- database: `tiktok_shop`

If `tiktok_shop` is unreadable, report the exact permission gap instead of inventing a proxy metric.

## Output Rules

When answering the user after querying:

1. State the exact statistic scope.
   - Example: `As of 2026-06-21 for task-creation data; as of 2026-06-20 for outbound fact tables`
2. Distinguish:
   - platform background
   - user-owned module data
3. If data is partial because of permissions, say so directly.
4. If June only has data until a mid-month date, mark it as partial month.

## Permission Diagnosis

Treat these as separate checks:

1. instance readable
2. database readable
3. table readable
4. SQL executable

Typical examples:

- instance readable, table denied:
  - ask for `instance.database.table` permission
- database denied:
  - ask for `instance.database` permission
- business mapping table denied:
  - explain that the metric path is confirmed in code but cannot be executed until permission is granted

## Pagination

Archery `limit_num` only caps the returned row count for one query result. When the mapping table may exceed one page, page explicitly in SQL.

Preferred pattern:

```sql
select distinct target_task_id
from t_smart_task_branch
where ...
order by target_task_id
limit 0, 200;
```

Then continue with:

```sql
limit 200, 200
limit 400, 200
limit 600, 200
```

Stop when the returned row count is less than the page size.

Use pagination whenever:

- the branch or mapping table may exceed 200 rows
- Archery row limits could truncate `task_id` discovery
- you need a complete set of IDs before aggregating in `stat_day_base`

## 常见报错

| 报错 | 原因 | 解决 |
|------|------|------|
| `Missing required environment variable` 之外提示找不到 `~/.archery_session.json` | 首次使用 / session 文件被删 | 跑 `archery_login.py` |
| HTTP 401 / 403 / 302 重定向到 `/login/` | session 过期 | 重跑 `archery_login.py` (脚本会自动提示) |
| `csrftoken=''` 或 CSRF 校验失败 | 登录后没抓到 csrftoken cookie | 重跑 `archery_login.py`, 确认登录成功 |
| MFA 输入框未找到 / TOTP 提交 disabled | TOTP 已过期 / 30s 窗口剩 <5s | 重跑 (脚本会主动等到新窗口) |
| `StaleElementReferenceException` | 页面重渲染 | 已用 `with_element` 重试, 不应再出现 |
| `Access denied for table ...` | 实例/库/表权限缺失 | 找 DBA 开权限, 不要绕过 |
| Chrome 启动失败 | driver 不匹配 | `pip install -U webdriver-manager` |

## Archery 2FA 页面踩坑

Archery 的 2FA 验证页 (`/login/2fa/`) 有几个非标设计, `archery_login.py` 已经做了专门处理:

1. **"验证" 按钮 id=`btnAuth`**, `type=button` (不是 submit!), class=`btn btn-success btn-block`
   - 普通 `button[type='submit']` selector 找不到它, 已加 `button#btnAuth` / `button.btn-success` 优先匹配
2. 页面上有 `'Google身份验证器'` tab 文字, `contains('验证')` 会误匹配它
   - 已用 id 精确锁定, 不依赖文字匹配
3. TOTP 输入框填值后, 按钮 disabled 状态不会自动切换
   - 必须 JS `dispatchEvent` 触发 `input` + `change` + `keyup` + `keydown` 事件
   - 单纯 `send_keys` 不触发 React/Vue onChange, 已强制走 JS 兜底
4. Archery 后端用 Django, cookies 共 3 个: `sessionid` (HttpOnly) + `csrftoken` + `acw_tc` (阿里云 WAF)
   - `sessionid` 是 Django session key, 必须带
   - `csrftoken` 同时要放 Cookie header 和 X-CSRFToken header
   - `acw_tc` 是阿里云 WAF 给的, 不带会被识别为机器人

## Session 有效性

- 跑一次 `archery_login.py` 写入的 `~/.archery_session.json` 通常能用 **数小时到 1 天** (Archery 默认 session 配置)
- `archery_query.py` 启动时会打印 `age=Xmin`, 超过 11 小时会标 ⚠ 提示重登
- 旧 session 失效时, requests 会收到 302 重定向到 `/login/`, 这时 `_parse_json` 会直接报错并提示跑 `archery_login.py`

## 脚本

- `scripts/archery_login.py` — 启 Chrome 自动登录 + MFA + 抓 session (写 `~/.archery_session.json`)
- `scripts/archery_query.py` — 用 session 直接 POST 查数据 (不依赖浏览器)
- `references/metric-patterns.md` — 业务查询模式 + SQL 模板

用 `python <script> --help` 查看完整参数。

## Reference

Read `references/metric-patterns.md` when you need example SQL templates and wording patterns for:

- new smart tasks
- domestic / overseas monthly trends
- `stat_day_base`
- permission request wording

