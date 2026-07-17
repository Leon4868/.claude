---
name: aliyun-sls-log-query
description: 查询阿里云 SLS 日志服务 (Log Service), 用于排查 data-center / AgentCC / 94AI 等微服务的线上日志。自动登录 RAM 用户 (账号+密码+VMFA TOTP 自动), 抓 cookies + 真实 x-csrf-token, 然后用 requests 直接 POST getLogs.json 取日志, 不依赖浏览器。当用户提到 SLS、阿里云日志、k8s-log-c4128cc88f92f4757a78daa9f542b2446、lognext、查日志、trace ID、请求链路、线上错误、data-center 服务、AgentccController、ai-admin 等场景, 或需要在没有 JumpServer / kubectl 时查生产日志, 使用本技能。
---

# 阿里云 SLS 日志查询

## 适用场景

- 用户问 "查一下 xxx 服务的日志"
- 提供 trace ID / 请求链路 / order ID / phone 后缀, 要定位错误
- 问 "线上有没有报 ERROR" / "xxx 时间点发生了什么"
- 直接给 SLS URL: `sls.console.aliyun.com/lognext/project/.../logsearch/...`
- JumpServer / kubectl 不可用, 但需要看生产日志
- 需要按时间窗口批量取日志做分析

**不适用**: 测试环境 K8S 日志 — 走 `k8s-jumpserver-log-triage` skill。

## 前置准备

凭证文件路径: `C:\Users\54542\.aliyun-credentials.json` (不进 git, 已配置好)

格式:
```json
{
  "username": "lianwukun@1985061268569924.onaliyun.com",
  "password": "xxx",
  "mfa_secret": "BASE32_TOTP_SEED",
  "target_url": "https://sls.console.aliyun.com/lognext/project/<project>/logsearch/<logstore>",
  "project": "k8s-log-c4128cc88f92f4757a78daa9f542b2446",
  "logstore": "datalogs",
  "default_query": "data-center | with_pack_meta"
}
```

依赖: `pip install selenium webdriver-manager pyotp requests` (首次需要)

## 工作流

### Step 1: 确认 session 是否还有效

```bash
python C:\Users\54542\.claude\skills\aliyun-sls-log-query\scripts\aliyun_sls_query.py --size 1
```

- 拿到日志 → session 有效, 直接进入 Step 3
- 报 `code: ConsoleNeedLogin` / `Invalid CSRF token` → session 过期, 走 Step 2
- 报找不到 `~/.aliyun_session.json` → 首次使用, 走 Step 2

### Step 2: 登录刷新 session (约 60 秒)

```bash
python C:\Users\54542\.claude\skills\aliyun-sls-log-query\scripts\aliyun_login.py
```

脚本会:
1. 启动 Chrome, 自动填账号/密码
2. TOTP 自动算 6 位 MFA 码 (`pyotp.TOTP(secret).now()`)
3. 自动跳过 "重置密码" 弹窗
4. 跳到 `target_url`, 抓 cookies + 真实 `x-csrf-token` (从页面 XHR 偷) 写到 `~/.aliyun_session.json`

**关键技巧**: `x-csrf-token` 不在 cookie 也不是简单 JS 变量, 是页面 axios 拦截器动态加的。脚本通过 CDP `goog:loggingPrefs: performance` 偷页面自己发的 XHR (`Network.requestWillBeSent` 事件) 抓出真实 header 值。

### Step 3: 查日志

```bash
# 最近 15 分钟, 默认查询
python .../aliyun_sls_query.py

# 最近 1 小时, 100 条
python .../aliyun_sls_query.py --minutes 60 --size 100

# 按 trace ID
python .../aliyun_sls_query.py --trace-id 6b62e9b764de5d45

# 按关键词
python .../aliyun_sls_query.py --keyword ERROR

# 自定义 SLS 查询语法
python .../aliyun_sls_query.py --query 'data-center and ERROR and "OrderService"'

# 指定时间窗口 (Unix 时间戳)
python .../aliyun_sls_query.py --from 1783392000 --to 1783395000

# 完整内容不截断 + 落盘
python .../aliyun_sls_query.py --full --out logs.json
```

**参数组合**: `--trace-id` 和 `--keyword` 会与 `--query` 用 `and` 组合。

### Step 4: 切换 project / logstore

默认 `k8s-log-c4128cc88f92f4757a78daa9f542b2446/datalogs` (94AI 线上 K8S 容器日志)。要查别的:

```bash
python .../aliyun_sls_query.py --project <other-project> --logstore <other-logstore> --query '*'
```

切回默认: 直接不带这俩参数即可。

## 工作流建议

### Trace ID 排查

```
1. 用户提供 trace ID (16 hex 字符)
2. python .../aliyun_sls_query.py --trace-id <id> --minutes 60 --size 50 --full --out trace.json
3. 解析 trace.json: 按 span 顺序看 SPRING_REQ → OKHTTP_REQ → OKHTTP_RESP → SPRING_RESP
4. 找 ERROR / Exception / 慢调用 (PerfLog 字段里有耗时)
5. 跨服务: 同一 trace ID 在不同服务里的 span, 拼出完整调用链
```

### 时间窗口策略

- 不知道时间: 先 `--minutes 60 --size 20` 探一次, 看日志最新时间戳
- 知道大致时间: 用 `--from`/`--to` 精确窗口, 避免漏掉
- 排查偶发问题: `--minutes 1440 --size 500 --out day.json` 拉全天再筛选

### 关键词组合

SLS 查询语法 (类似 Kibana KQL, 但有差异):
- `data-center` — 必含 `data-center` 的日志 (服务名)
- `ERROR and "OrderService"` — ERROR 且包含 OrderService
- `not DEBUG` — 排除 DEBUG 级别
- `__tag__:_namespace_ = "default"` — 按 K8S namespace 过滤
- `* | with_pack_meta` — `*` 是查询, `with_pack_meta` 是把同秒日志合并显示

默认 `default_query` 是 `data-center | with_pack_meta` — 查 94AI data-center 服务的全部日志。

## 常见报错

| 报错 | 原因 | 解决 |
|------|------|------|
| `ConsoleNeedLogin` / `Invalid CSRF token` | session 过期 | 跑 `aliyun_login.py` |
| 找不到 `~/.aliyun_session.json` | 首次使用 | 跑 `aliyun_login.py` |
| 找不到 `~/.aliyun-credentials.json` | 凭证未配 | 按 "前置准备" 创建 |
| MFA 提交后页面没反应 | TOTP 已过期 | 重新跑 (脚本会等新 30s 窗口) |
| `StaleElementReferenceException` | 页面重渲染过快 | 已用 `with_element` 重试, 不应再出现 |
| Chrome 启动失败 | driver 不匹配 | `pip install -U webdriver-manager` |

## 已知信息

- **目标账号**: `lianwukun@1985061268569924.onaliyun.com` (94AI RAM 子账号)
- **主账号 alias**: `1985061268569924.onaliyun.com` (URL path 里那段)
- **MFA 类型**: VMFA (虚拟 MFA), TOTP 标准 6 位 30 秒
- **登录后强制弹窗**: 重置密码 (周期性), 必须点 "跳过重置"
- **目标 project**: `k8s-log-c4128cc88f92f4757a78daa9f542b2446` (94AI 生产 K8S 容器日志)
- **目标 logstore**: `datalogs` (应用日志)
- **常见服务名 (作为 query)**: `data-center`, `ai-admin`, `ai-decision-system`, `company-aggre`, `call-task`, `agentcc`
- **抓包参考**: `D:\prompt\业务配置\SLS-2026-07-07.json` 含一次完整登录+查询的真实流量

## 脚本

- `scripts/aliyun_login.py` — 启 Chrome 自动登录 + 抓 session
- `scripts/aliyun_sls_query.py` — 直接 POST 查日志 (不依赖浏览器)

用 `python <script> --help` 查看完整参数。
