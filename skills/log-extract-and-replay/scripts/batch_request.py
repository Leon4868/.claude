#!/usr/bin/env python3
"""
批量 HTTP 请求执行脚本

从 JSON 文件读取数据，逐条发送 POST 请求，累加响应中的指定字段。

用法:
    python3 batch_request.py --file data.json --url URL --header "Key: Value" --sum-field fieldName

参数:
    --file       JSON 数据文件路径（数组格式）
    --url        目标 API URL
    --header     请求头（可多次指定）
    --sum-field  需要累加的响应字段名
    --start      起始索引（从 0 开始，用于断点续传）
    --dry-run    仅打印第一条请求，不实际发送
"""

import json
import urllib.request
import urllib.error
import argparse
import sys
import time


def send_request(url, headers_dict, body_data, timeout=30):
    body = json.dumps(body_data, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers_dict, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description='批量 HTTP POST 请求执行工具')
    parser.add_argument('--file', required=True, help='JSON 数据文件路径')
    parser.add_argument('--url', required=True, help='目标 API URL')
    parser.add_argument('--header', action='append', default=[], help='请求头 (格式: "Key: Value")')
    parser.add_argument('--sum-field', help='需要累加的响应字段名')
    parser.add_argument('--start', type=int, default=0, help='起始索引 (默认 0)')
    parser.add_argument('--dry-run', action='store_true', help='仅打印第一条请求')
    args = parser.parse_args()

    # 读取数据
    with open(args.file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("错误: JSON 文件内容必须是数组格式")
        sys.exit(1)

    total_records = len(data)
    print(f"共 {total_records} 条记录")

    # 解析请求头
    headers_dict = {'Content-Type': 'application/json'}
    for h in args.header:
        key, _, value = h.partition(':')
        headers_dict[key.strip()] = value.strip()

    # dry-run 模式
    if args.dry_run:
        print(f"\n[Dry Run] URL: {args.url}")
        print(f"[Dry Run] Headers: {json.dumps(headers_dict, indent=2)}")
        print(f"[Dry Run] Body (第1条):")
        print(json.dumps(data[0], ensure_ascii=False, indent=2)[:2000])
        return

    # 执行请求
    total_sum = 0
    success_count = 0
    fail_count = 0
    failed_records = []

    for i in range(args.start, total_records):
        record = data[i]
        seq = i + 1
        try:
            result = send_request(args.url, headers_dict, record)
            success_count += 1

            if args.sum_field and args.sum_field in result:
                val = result[args.sum_field]
                total_sum += val

            if seq % 50 == 0 or seq == total_records:
                msg = f"[{seq}/{total_records}] 成功={success_count}"
                if args.sum_field:
                    msg += f", 累计 {args.sum_field}={total_sum}"
                print(msg)

        except Exception as e:
            fail_count += 1
            failed_records.append({'index': i, 'error': str(e)})
            print(f"[{seq}/{total_records}] 失败: {e}")

    # 汇总
    print(f"\n===== 执行完毕 =====")
    print(f"总数: {total_records}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    if args.sum_field:
        print(f"总 {args.sum_field}: {total_sum}")

    if failed_records:
        print(f"\n失败列表:")
        for fr in failed_records:
            print(f"  [index={fr['index']}] {fr['error']}")


if __name__ == '__main__':
    main()
