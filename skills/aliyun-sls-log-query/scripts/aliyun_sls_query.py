"""Aliyun SLS 日志查询脚本 - 用 ~/.aliyun_session.json 直接 POST 取日志, 无需浏览器。

前置: 先运行 aliyun_login.py 完成登录并抓 session。

用法:
    python aliyun_sls_query.py                                # 默认查最近 15 分钟
    python aliyun_sls_query.py --minutes 60 --size 50
    python aliyun_sls_query.py --query 'ERROR and data-center'
    python aliyun_sls_query.py --trace-id 6b62e9b764de5d45
    python aliyun_sls_query.py --out logs.json
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
from pathlib import Path

import requests

CRED_FILE = Path.home() / ".aliyun-credentials.json"
SESSION_FILE = Path.home() / ".aliyun_session.json"
GET_LOGS_URL = "https://sls.console.aliyun.com/console/logs/getLogs.json"


def load_creds() -> dict:
    if not CRED_FILE.exists():
        sys.exit(f"[!] 凭证文件不存在: {CRED_FILE}")
    return json.loads(CRED_FILE.read_text(encoding="utf-8"))


def load_session() -> dict:
    if not SESSION_FILE.exists():
        sys.exit(
            f"[!] 找不到 session 文件: {SESSION_FILE}\n请先运行 aliyun_login.py 完成登录"
        )
    return json.loads(SESSION_FILE.read_text(encoding="utf-8"))


def gen_trace_ids() -> tuple[str, str, str]:
    trace = secrets.token_hex(16)
    span = secrets.token_hex(8)
    return (
        f"{trace}-{span}-1",
        f"00-{trace}-{span}-01",
        f"{trace}:{span}:0:1",
    )


def query_logs(
    session: dict,
    creds: dict,
    *,
    minutes: int = 15,
    query: str | None = None,
    size: int = 20,
    project: str | None = None,
    logstore: str | None = None,
    from_ts: int | None = None,
    to_ts: int | None = None,
) -> dict:
    project = project or creds.get("project", "")
    logstore = logstore or creds.get("logstore", "")
    query = query or creds.get("default_query", "*")

    now = int(time.time())
    body = {
        "ProjectName": project,
        "LogStoreName": logstore,
        "from": from_ts if from_ts else now - minutes * 60,
        "to": to_ts if to_ts else now,
        "query": query,
        "Page": 1,
        "Size": size,
        "Reverse": "true",
        "pSql": "false",
        "fullComplete": "false",
        "schemaFree": "false",
        "needHighlight": "true",
    }

    b3, traceparent, uber = gen_trace_ids()
    headers = {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9",
        "b3": b3,
        "bx-v": "2.5.36",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://sls.console.aliyun.com",
        "priority": "u=1, i",
        "referer": f"https://sls.console.aliyun.com/lognext/project/{project}/logsearch/{logstore}",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "traceparent": traceparent,
        "uber-trace-id": uber,
        "user-agent": session.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        ),
        "x-csrf-token": session.get("csrf", ""),
    }

    resp = requests.post(
        GET_LOGS_URL,
        data=body,
        headers=headers,
        cookies=session.get("cookies", {}),
        timeout=30,
    )
    print(f"[*] POST {GET_LOGS_URL} -> {resp.status_code}")
    if resp.status_code != 200:
        print(f"[!] 响应: {resp.text[:500]}")
        resp.raise_for_status()
    return resp.json()


def main() -> int:
    creds = load_creds()
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=15, help="查询时间窗口(分钟)")
    parser.add_argument("--from", dest="from_ts", type=int, help="起始 Unix 时间戳(秒)")
    parser.add_argument("--to", dest="to_ts", type=int, help="结束 Unix 时间戳(秒)")
    parser.add_argument("--query", default=None, help="SLS 查询语句, 默认读 credentials")
    parser.add_argument("--trace-id", default=None, help="按 trace ID 过滤 (等价 --query)")
    parser.add_argument("--keyword", default=None, help="关键词 (等价 --query 'KW')")
    parser.add_argument("--size", type=int, default=20, help="返回条数")
    parser.add_argument("--project", default=None)
    parser.add_argument("--logstore", default=None)
    parser.add_argument("--out", help="保存原始 JSON 到该文件")
    parser.add_argument("--full", action="store_true", help="打印完整日志内容(不截断)")
    args = parser.parse_args()

    # 组合 query
    q = args.query
    if args.trace_id:
        q = args.trace_id if not q else f"{q} and \"{args.trace_id}\""
    elif args.keyword:
        q = args.keyword if not q else f"{q} and {args.keyword}"

    session = load_session()
    print(
        f"[*] Session: csrf={session.get('csrf','')[:12]!r}, "
        f"cookies={len(session.get('cookies', {}))}, "
        f"age={int(time.time() - session.get('saved_at', time.time()))}s"
    )

    data = query_logs(
        session, creds,
        minutes=args.minutes,
        query=q,
        size=args.size,
        project=args.project,
        logstore=args.logstore,
        from_ts=args.from_ts,
        to_ts=args.to_ts,
    )

    if isinstance(data, dict):
        print(f"[*] 响应 keys: {list(data.keys())}")
        # 兼容多种返回字段名
        logs = data.get("data") or data.get("logs") or data.get("items") or []
        print(f"[+] 拿到 {len(logs)} 条日志\n")
        if args.out:
            Path(args.out).write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"[+] 完整响应已写入 {args.out}\n")
        for i, log in enumerate(logs):
            ts = log.get("__time__") or log.get("time") or "?"
            content = (
                log.get("content")
                or log.get("message")
                or log.get("__content__")
                or json.dumps(log, ensure_ascii=False)
            )
            if isinstance(content, str) and not args.full:
                content = content[:300]
            print(f"[{i}] {ts} {content}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
