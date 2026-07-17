# Metric Patterns

## Environment

Set these environment variables locally before using the script:

```text
ARCHERY_BASE_URL
ARCHERY_CSRF_TOKEN
ARCHERY_COOKIE
```

On Windows, `scripts/archery_query.py` reads the current process first, then `HKCU\Environment`, then machine-level environment variables if present.

Example PowerShell setup:

```powershell
$env:ARCHERY_BASE_URL = "https://archery-k8s.94ai.pro"
$env:ARCHERY_CSRF_TOKEN = "your-csrf-token"
$env:ARCHERY_COOKIE = "_ga=...; csrftoken=...; sessionid=...; ..."
```

Persistent user-variable setup:

```powershell
[Environment]::SetEnvironmentVariable("ARCHERY_BASE_URL", "https://archery-k8s.94ai.pro", "User")
[Environment]::SetEnvironmentVariable("ARCHERY_CSRF_TOKEN", "your-csrf-token", "User")
[Environment]::SetEnvironmentVariable("ARCHERY_COOKIE", "_ga=...; csrftoken=...; sessionid=...; ...", "User")
```

## Instance Discovery

List readable instances:

```powershell
python scripts/archery_query.py list-instances
```

List databases:

```powershell
python scripts/archery_query.py list-databases --instance "main-db"
```

List tables:

```powershell
python scripts/archery_query.py list-tables --instance "main-db" --database "ai_admin"
```

## New Smart Task

Important distinction:

- New smart-task count = deduplicated smart-task ID count.
- In the current `ai.ai_task` data path, use `count(distinct flow_id)` for the smart-task count.
- `ai_task.task_id` is the node outbound-task ID. Use it only to map to `stat_day_base.task_id` for outbound volume.
- Do not use `count(*)` or `count(distinct task_id)` from `ai_task` as the new smart-task count.

### H1 smart-task count

Use `count(distinct flow_id)` as the smart-task count. Do not use `count(*)` from `ai_task` as the report task count.

```sql
select
  count(distinct flow_id) as smart_task_cnt,
  count(distinct company_id) as company_cnt
from ai_task
where create_time >= '2026-01-01'
  and create_time < '2026-07-01'
  and flow_id is not null;
```

### Monthly trend

```sql
select
  date_format(create_time, '%Y-%m') as month,
  count(distinct flow_id) as smart_task_cnt
from ai_task
where create_time >= '2026-01-01'
  and create_time < '2026-07-01'
  and flow_id is not null
group by date_format(create_time, '%Y-%m')
order by month;
```

### H1 outbound volume

Use the smart-task ID scope for task counts, then map its node outbound tasks to facts:

```sql
select task_id
from ai_task
where create_time >= '2026-01-01'
  and create_time < '2026-07-01'
  and flow_id is not null;
```

Then aggregate `stat_day_base` by the collected node `task_id` list. Keep the wording explicit: task count is by smart-task ID; outbound volume is by associated node outbound tasks.

## Legacy Smart Task

### Domestic task count

```sql
select
  count(*) as smart_task_cnt,
  count(distinct company_id) as company_cnt
from t_smart_task
where create_time >= '2026-01-01'
  and create_time < '2026-07-01';
```

### Domestic branch mapping count

```sql
select
  count(*) as branch_cnt,
  count(distinct target_task_id) as target_task_cnt
from t_smart_task_branch
where target_task_id is not null
  and task_id in (
    select id
    from t_smart_task
    where create_time >= '2026-01-01'
      and create_time < '2026-07-01'
  );
```

### Domestic fact aggregation

Use:

- `auto-db.ai_task.t_smart_task`
- `auto-db.ai_task.t_smart_task_branch`
- `log-db.auto_dialer_data.stat_day_base`

Aggregate with mapped outbound task IDs:

```sql
select
  count(distinct task_id) as task_cnt,
  sum(import_number_count) as import_number_count,
  sum(call_number_count) as call_number_count
from stat_day_base
where stat_date >= '2026-01-01'
  and stat_date < '2026-07-01'
  and task_id in (...mapped target_task_id list...);
```

### Overseas fact aggregation

Use the same logic, but keep the task table, branch table, and `stat_day_base` in the overseas production instance.

## `stat_day_base`

Use only when the business scope is confirmed. Do not assume it is a full platform total.

### Aggregate template

```sql
select
  count(distinct company_id) as company_cnt,
  sum(import_number_count) as import_number_count,
  sum(call_number_count) as call_number_count,
  sum(call_count) as call_count,
  sum(answer_count) as answer_count,
  sum(ab_count) as ab_count,
  sum(sms_count) as sms_count
from stat_day_base
where stat_date >= '2026-01-01'
  and stat_date < '2026-07-01';
```

### Monthly trend

```sql
select
  date_format(stat_date, '%Y-%m') as month,
  sum(import_number_count) as import_number_count,
  sum(call_number_count) as call_number_count,
  sum(answer_count) as answer_count,
  sum(ab_count) as ab_count,
  sum(sms_count) as sms_count
from stat_day_base
where stat_date >= '2026-01-01'
  and stat_date < '2026-07-01'
group by date_format(stat_date, '%Y-%m')
order by month;
```

## TikTok Shop

Known metric split path:

```text
polardb-tidb.tiktok_shop.t_shop_task.task_id -> stat_day_base.task_id
```

Recommended flow:

1. Query `t_shop_task` and identify the relevant `task_id`
2. Filter `stat_day_base` by those `task_id`
3. Aggregate by month, `task_scene_id`, or `type` if needed

If `tiktok_shop` is denied, do not estimate from unrelated fields. Ask for:

```text
polardb-tidb.tiktok_shop.t_shop_task
polardb-tidb.tiktok_shop.t_scene_config
```

## Permission Wording

Use direct wording like:

- `The metric path is confirmed, but read access to main-db.tiktok_shop.t_shop_task is missing, so TikTok Shop tasks cannot yet be mapped to stat_day_base.task_id.`
- `Only the total new smart-task dataset is currently available; TikTok Shop cannot yet be split out as a separate metric.`

## Pagination Pattern

When the mapping set may be larger than one page, page through the source IDs first:

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

Collect all returned IDs, deduplicate them, then run the final aggregate query against `stat_day_base`.

## Scope Wording

Use explicit dates:

- `As of 2026-06-21, task-creation data is current through 2026-06-21.`
- `As of 2026-06-21, outbound and settlement fact tables are current through 2026-06-20.`

Use attribution wording:

- `These metrics are reported only as business results for the user's owned module, not as ownership of the entire platform total.`

