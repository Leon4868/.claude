#!/usr/bin/env python
"""Archery 只读查询脚本。

凭证加载优先级 (高 → 低):
1. ~/.archery_session.json (由 archery_login.py 自动生成, 推荐)
2. 进程环境变量 ARCHERY_BASE_URL / ARCHERY_CSRF_TOKEN / ARCHERY_COOKIE
3. Windows 用户级注册表 (HKCU\\Environment)
4. Windows 机器级注册表 (HKLM\\...\\Environment)

session 文件不存在时, 提示用户先跑 archery_login.py。
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

SESSION_FILE = Path.home() / ".archery_session.json"
SESSION_MAX_AGE = 11 * 3600  # 11 小时视为过期 (Archery session 默认比这长, 但 csrf/cookie 中间件可能更短)


def read_windows_user_env(name: str) -> Optional[str]:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value) if value else None
    except OSError:
        return None


def read_windows_machine_env(name: str) -> Optional[str]:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value) if value else None
    except OSError:
        return None


def read_env(name: str) -> Optional[str]:
    value = os.environ.get(name)
    if not value:
        value = read_windows_user_env(name)
    if not value:
        value = read_windows_machine_env(name)
    return value


def load_session_file() -> Optional[dict]:
    """读 ~/.archery_session.json。返回 None 表示文件不存在。"""
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[!] session 文件解析失败 ({exc}), 改用环境变量", file=sys.stderr)
        return None


def resolve_credentials() -> dict:
    """优先用 session 文件, 缺字段时用环境变量补。"""
    sess = load_session_file()

    base_url = (sess or {}).get("base_url") or read_env("ARCHERY_BASE_URL")
    csrf_token = (sess or {}).get("csrf_token") or read_env("ARCHERY_CSRF_TOKEN")
    cookie_str = (sess or {}).get("cookie") or read_env("ARCHERY_COOKIE")
    cookies_dict = (sess or {}).get("cookies_dict") or {}

    source = "session-file"
    if not sess:
        source = "env"
        if not (base_url and csrf_token and cookie_str):
            raise SystemExit(
                f"[!] 找不到凭证。请先跑:\n"
                f"    python {Path(__file__).parent / 'archery_login.py'}\n"
                f"    (会自动生成 {SESSION_FILE})\n"
                f"    或者手动设置环境变量 ARCHERY_BASE_URL / ARCHERY_CSRF_TOKEN / ARCHERY_COOKIE"
            )

    if not base_url:
        raise SystemExit("[!] 缺少 base_url (session 文件损坏或环境变量未设)")

    # session 文件有 age, 提示过期风险
    age_hint = ""
    if sess and sess.get("saved_at"):
        age = int(time.time() - sess["saved_at"])
        if age > SESSION_MAX_AGE:
            age_hint = f" ⚠ age={age//3600}h 建议重跑 archery_login.py"
        else:
            age_hint = f" age={age//60}min"

    print(
        f"[*] 凭证来源: {source} | cookies={len(cookies_dict)} | "
        f"csrftoken={(csrf_token or '')[:12]!r}{age_hint}",
        file=sys.stderr,
    )
    return {
        "base_url": base_url.rstrip("/"),
        "csrf_token": csrf_token,
        "cookie": cookie_str,
        "cookies_dict": cookies_dict,
    }


class ArcheryClient:
    def __init__(self) -> None:
        cred = resolve_credentials()
        self.base_url = cred["base_url"]
        self.csrf_token = cred["csrf_token"]
        self.cookie = cred["cookie"]
        self.cookies_dict = cred["cookies_dict"]
        self.session = requests.Session()
        self.common_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"{self.base_url}/sqlquery/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
            "X-CSRFToken": self.csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

    def _cookies_for_request(self) -> Dict[str, str]:
        """优先用 dict 形式 (session 文件提供); 否则解析 cookie 字符串。"""
        if self.cookies_dict:
            return dict(self.cookies_dict)
        parsed: Dict[str, str] = {}
        if self.cookie:
            for kv in self.cookie.split(";"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    parsed[k.strip()] = v.strip()
        return parsed

    def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self.common_headers,
            cookies=self._cookies_for_request(),
            timeout=60,
        )
        response.raise_for_status()
        return self._parse_json(response)

    def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        headers = dict(self.common_headers)
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        response = self.session.post(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            cookies=self._cookies_for_request(),
            timeout=120,
        )
        response.raise_for_status()
        return self._parse_json(response)

    @staticmethod
    def _parse_json(response) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception:
            # 响应不是 JSON 多半是被重定向到了登录页 (session 失效)
            body_head = (response.text or "")[:200].replace("\n", " ")
            raise SystemExit(
                f"[!] 响应不是 JSON, 多半 session 已失效被重定向到登录页。\n"
                f"    HTTP {response.status_code}, URL={response.url}\n"
                f"    body 头 200 字: {body_head!r}\n"
                f"    → 重跑: python {Path(__file__).parent / 'archery_login.py'}"
            )

    def list_instances(self) -> Dict[str, Any]:
        return self.get("/group/user_all_instances/", {"tag_codes[]": "can_read"})

    def list_databases(self, instance: str) -> Dict[str, Any]:
        return self.get(
            "/instance/instance_resource/",
            {"instance_name": instance, "resource_type": "database"},
        )

    def list_tables(self, instance: str, database: str) -> Dict[str, Any]:
        return self.get(
            "/instance/instance_resource/",
            {
                "instance_name": instance,
                "db_name": database,
                "resource_type": "table",
            },
        )

    def query(
        self,
        instance: str,
        database: str,
        sql: str,
        table: str = "",
        limit: int = 200,
    ) -> Dict[str, Any]:
        return self.post(
            "/query/",
            {
                "instance_name": instance,
                "db_name": database,
                "schema_name": "",
                "tb_name": table,
                "sql_content": sql,
                "limit_num": str(limit),
            },
        )


def ensure_read_only(sql: str) -> None:
    stripped = sql.strip().lower()
    allowed = ("select", "show", "desc", "describe", "explain", "with")
    if not stripped.startswith(allowed):
        raise SystemExit("Only read-only SQL is allowed by this script.")


def format_rows_as_table(columns: List[str], rows: Iterable[Iterable[Any]]) -> str:
    str_rows = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    widths = [len(col) for col in columns]
    for row in str_rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    line = " | ".join(col.ljust(widths[idx]) for idx, col in enumerate(columns))
    sep = "-+-".join("-" * widths[idx] for idx in range(len(columns)))
    body = [
        " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))
        for row in str_rows
    ]
    return "\n".join([line, sep, *body])


def print_resource_result(result: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    data = result.get("data")
    if isinstance(data, list):
        for item in data:
            print(item)
        return

    if isinstance(data, dict):
        print(format_rows_as_table(list(data.keys()), [data.values()]))
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


def print_query_result(result: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("status") != 0:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    data = result.get("data", {})
    columns = data.get("column_list", [])
    rows = data.get("rows", [])
    if not columns:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(format_rows_as_table(columns, rows))


def cmd_list_instances(client: ArcheryClient, args: argparse.Namespace) -> None:
    result = client.list_instances()
    print_resource_result(result, args.format)


def cmd_list_databases(client: ArcheryClient, args: argparse.Namespace) -> None:
    result = client.list_databases(args.instance)
    print_resource_result(result, args.format)


def cmd_list_tables(client: ArcheryClient, args: argparse.Namespace) -> None:
    result = client.list_tables(args.instance, args.database)
    print_resource_result(result, args.format)


def cmd_query(client: ArcheryClient, args: argparse.Namespace) -> None:
    ensure_read_only(args.sql)
    result = client.query(
        instance=args.instance,
        database=args.database,
        sql=args.sql,
        table=args.table or "",
        limit=args.limit,
    )
    print_query_result(result, args.format)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Archery helper for production data discovery and querying."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_instances = subparsers.add_parser("list-instances")
    parser_instances.add_argument("--format", choices=["table", "json"], default="table")
    parser_instances.set_defaults(func=cmd_list_instances)

    parser_databases = subparsers.add_parser("list-databases")
    parser_databases.add_argument("--instance", required=True)
    parser_databases.add_argument("--format", choices=["table", "json"], default="table")
    parser_databases.set_defaults(func=cmd_list_databases)

    parser_tables = subparsers.add_parser("list-tables")
    parser_tables.add_argument("--instance", required=True)
    parser_tables.add_argument("--database", required=True)
    parser_tables.add_argument("--format", choices=["table", "json"], default="table")
    parser_tables.set_defaults(func=cmd_list_tables)

    parser_query = subparsers.add_parser("query")
    parser_query.add_argument("--instance", required=True)
    parser_query.add_argument("--database", required=True)
    parser_query.add_argument("--table", default="")
    parser_query.add_argument("--sql", required=True)
    parser_query.add_argument("--limit", type=int, default=200)
    parser_query.add_argument("--format", choices=["table", "json"], default="table")
    parser_query.set_defaults(func=cmd_query)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    client = ArcheryClient()
    args.func(client, args)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text, file=sys.stderr)
        # 403 / 401 / 302 → login 一般是 session 过期, 直接提示重登
        if exc.response is not None and exc.response.status_code in (401, 403, 302):
            print(
                f"[!] session 可能已过期, 重跑:\n"
                f"    python {Path(__file__).parent / 'archery_login.py'}",
                file=sys.stderr,
            )
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
