---
name: log-extract-and-replay
description: "从日志文件（如阿里云 SLS 导出的 JSON）中提取 params 字段数据，保存为 JSON 文件，统计数据量，并可组装为批量 HTTP 请求逐条执行、累加响应结果。适用于日志数据提取、API 请求重放、批量数据导入、日志分析等场景。当用户提到从日志提取数据、批量请求、API 重放、日志解析、批量 cURL、批量导入等关键词时触发。"
---

# 日志数据提取与 API 重放

## 概述

从阿里云 SLS 导出的日志 JSON 文件中提取 `params` 字段数据，保存为 JSON 文件，并支持将提取的数据组装为批量 HTTP 请求执行。完整流程分为四个阶段：提取、保存、统计、执行。

## 工作流程

### 阶段一：提取 params 数据

日志文件中每行是一条 JSON 记录，`params` 嵌套在 `log` 字段内部，存在多层转义。

提取步骤：
1. 用 `grep -c "params"` 统计出现次数确认数据量
2. 逐行解析外层 JSON，获取 `log` 字段
3. 在 `log` 内容中用正则提取 `"params":"..."` 的值
4. 多层反转义后解析为 JSON 对象

```python
import json, re

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

all_params = []
for line in lines:
    record = json.loads(line.strip())
    log_content = record.get('log', '')
    match = re.search(r'"params"\s*:\s*"((?:[^"\\]|\\.)*)"', log_content)
    if match:
        params_str = match.group(1)
        unescaped = params_str.replace('\\\\', '\x00').replace('\\"', '"').replace('\\/', '/').replace('\x00', '\\')
        data = json.loads(unescaped)
        all_params.append(data)
```

**识别要点：**
- 先检查文件大小，大文件使用逐行读取或 grep 定位
- 取样查看实际格式（前几个匹配）后再确认解析策略

### 阶段二：保存为 JSON

将提取的 params 数据保存为 JSON 文件，命名规则：`{原文件名}_params.json`

```python
out_path = input_file.replace('.json', '_params.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(all_params, f, ensure_ascii=False, indent=2)
```

### 阶段三：数据统计

对提取的数据进行基础统计，帮助用户确认数据完整性。

常见统计项：
- params 记录总数
- 嵌套数组元素总数（如 `customers` 总数）
- 字段分布（min/max/avg）

```python
total_items = sum(len(item.get('customers', [])) for item in data)
```

### 阶段四：批量请求执行

将提取的 params 数据组装为 HTTP POST 请求并逐条执行。

**重要：执行前必须向用户索要 `x-access-token` 值，不得使用硬编码的 token。**

**执行策略：**
1. 向用户询问 `x-access-token` 的值
2. 先发送第一条请求确认接口响应格式
3. 确认成功后再批量执行剩余请求
4. 每 50 条打印一次进度
5. 失败请求记录日志但不中断执行
6. 最终汇总：成功数、失败数、累加值

**可直接使用 `scripts/batch_request.py` 脚本执行批量请求。**

用法：
```bash
python3 scripts/batch_request.py \
  --file data_params.json \
  --url "http://openapi.94ai.com/v1/task/importTaskCustomer" \
  --header "x-access-token: <用户提供的token>" \
  --sum-field importNum
```

或者内联执行：

```python
import json, urllib.request

url = 'http://openapi.94ai.com/v1/task/importTaskCustomer'
headers = {
    'x-access-token': '<用户提供的token>',
    'Content-Type': 'application/json'
}

total = 0
success = 0
fail = 0

for i, record in enumerate(data, start=1):
    body = json.dumps(record, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            total += result.get('importNum', 0)
            success += 1
            if i % 50 == 0 or i == len(data):
                print(f"[{i}/{len(data)}] 累计 importNum={total}")
    except Exception as e:
        fail += 1
        print(f"[{i}/{len(data)}] 失败: {e}")

print(f"成功: {success}, 失败: {fail}, 总 importNum: {total}")
```

## 注意事项

- 使用 `urllib.request` 而非 `requests` 库，避免依赖安装问题
- 大文件（>256KB）无法一次性读取，使用 `grep` 定位或分段读取
- 批量请求前务必先单条测试确认接口正常
- 设置合理的 timeout（建议 30 秒）
- `x-access-token` 必须由用户提供，禁止硬编码或使用历史 token
- 对于生产环境接口，执行前确认操作是否可逆
