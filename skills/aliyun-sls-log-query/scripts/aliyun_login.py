"""Aliyun SLS 自动登录 + session 抓取脚本。

用法:
    python aliyun_login.py

凭证从 ~/.aliyun-credentials.json 读取, 不进 git。

流程:
1. Selenium 打开 Chrome, 自动填账号/密码
2. TOTP 自动算 6 位 MFA 码并填入
3. 自动跳过 '重置密码' 提示
4. 跳到 SLS 日志检索页
5. 抓 cookies + x-csrf-token (从页面 XHR 偷) 写到 ~/.aliyun_session.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlparse

import pyotp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

CRED_FILE = Path.home() / ".aliyun-credentials.json"
SESSION_FILE = Path.home() / ".aliyun_session.json"


def load_creds() -> dict:
    if not CRED_FILE.exists():
        sys.exit(
            f"[!] 凭证文件不存在: {CRED_FILE}\n"
            "请创建如下格式的 JSON:\n"
            "{\n"
            '  "username": "xxx@xxx.onaliyun.com",\n'
            '  "password": "xxx",\n'
            '  "mfa_secret": "BASE32_TOTP_SECRET",\n'
            '  "target_url": "https://sls.console.aliyun.com/lognext/project/<p>/logsearch/<l>",\n'
            '  "project": "<project>",\n'
            '  "logstore": "<logstore>",\n'
            '  "default_query": "<query>"\n'
            "}"
        )
    return json.loads(CRED_FILE.read_text(encoding="utf-8"))


SELECTORS = {
    "username": [
        "input#loginName",
        "input[name='LoginName']",
        "input#account",
        "input[name='account']",
        "input[placeholder*='账号']",
        "input[placeholder*='邮箱']",
    ],
    "password": [
        "input#loginPassword",
        "input[name='Password']",
        "input#password",
        "input[type='password']",
    ],
    "submit": [
        "button.login-btn",
        "button[type='submit']",
        "button.fui-btn-primary",
        "button.password-login",
    ],
    "mfa_code": [
        "input[placeholder*='6 位数字']",
        "input[placeholder*='安全码']",
        "input[placeholder*='6-digit security' i]",
        "input#authCode",
        "input[name='authCode']",
    ],
    "mfa_submit": [
        "button.next-btn-primary",
        "button[type='submit']",
        "button.submit",
        "button.verify-btn",
    ],
    "skip_reset_css": ["button.skip", "a.skip"],
}

BUTTON_TEXT = {
    "mfa_submit": ["提交验证", "确定", "验证", "Confirm", "Verify"],
    "skip_reset": ["跳过重置", "跳过", "暂不修改", "以后再说", "Skip"],
    "submit": ["登录", "下一步", "Sign in", "Next"],
}


def find_first(driver, selectors, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for sel in selectors:
            try:
                for el in driver.find_elements(By.CSS_SELECTOR, sel):
                    if el.is_displayed() and el.is_enabled():
                        return el
            except Exception:
                continue
        time.sleep(0.4)
    return None


def find_button_by_text(driver, texts, timeout=8):
    end = time.time() + timeout
    while time.time() < end:
        for t in texts:
            for tag in ("button", "a", "span", "div"):
                try:
                    els = driver.find_elements(
                        By.XPATH,
                        f"//{tag}[contains(normalize-space(string(.)),'{t}')]",
                    )
                    for el in els:
                        if not (el.is_displayed() and el.is_enabled()):
                            continue
                        if tag in ("button", "a"):
                            return el
                        parent = el.find_element(By.XPATH, "..").tag_name
                        if parent in ("button", "a"):
                            return el
                except Exception:
                    continue
        time.sleep(0.4)
    return None


def with_element(driver, selectors, action, attempts=12, delay=0.4):
    """每次重试都重新查找元素, 解决 Next Loading overlay 频繁重渲染导致的 stale。"""
    from selenium.common.exceptions import StaleElementReferenceException

    for _ in range(attempts):
        for sel in selectors:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
            except Exception:
                continue
            for el in els:
                try:
                    if not (el.is_displayed() and el.is_enabled()):
                        continue
                except Exception:
                    continue
                try:
                    r = action(el)
                    if r is not None:
                        return r
                except StaleElementReferenceException:
                    break
                except Exception:
                    continue
        time.sleep(delay)
    return None


def human_type(element, text):
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.DELETE)
    element.send_keys(text)


def dump_session(driver) -> dict | None:
    """抓所有域 cookies + 多方位扫描 csrf, 写到 SESSION_FILE。"""
    try:
        time.sleep(2.0)
        all_cookies = driver.execute_cdp_cmd("Network.getAllCookies", {}).get("cookies", [])
        all_cookies.extend(driver.get_cookies())
        seen, merged = set(), []
        for c in all_cookies:
            key = (c.get("name"), c.get("domain"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(c)

        csrf = ""
        try:
            csrf = driver.execute_script(
                """
                const cand = [
                    window._csrf_token_, window.csrfToken, window.csrf_token, window.xCsrfToken,
                    window.__INITIAL_STATE__ && window.__INITIAL_STATE__.csrfToken,
                    window.__NEXT_DATA__ && window.__NEXT_DATA__.props && window.__NEXT_DATA__.props.csrfToken,
                    window.aliyun_meta && window.aliyun_meta.csrfToken,
                ].filter(Boolean);
                if (cand.length) return cand[0];
                for (const sel of ['meta[name="csrf-token"]','meta[name="x-csrf-token"]','meta[name="X-CSRF-Token"]','meta[http-equiv="x-csrf-token"]']) {
                    const m = document.querySelector(sel);
                    if (m && m.content) return m.content;
                }
                if (window.axios && window.axios.defaults && window.axios.defaults.headers) {
                    const h = window.axios.defaults.headers.common || {};
                    if (h['x-csrf-token']) return h['x-csrf-token'];
                    if (h['X-CSRF-Token']) return h['X-CSRF-Token'];
                }
                const html = document.documentElement.outerHTML;
                const m = html.match(/["']?x-csrf-token["']?\\s*[:=]\\s*["']([a-f0-9]{8,40})["']/i);
                if (m) return m[1];
                return '';
                """
            ) or ""
        except Exception:
            pass

        if not csrf:
            try:
                for store in ("localStorage", "sessionStorage"):
                    found = driver.execute_script(
                        f"const out={{}};for(let i=0;i<{store}.length;i++){{const k={store}.key(i);if(/csrf|token|xsrf/i.test(k))out[k]={store}.getItem(k);}}return out;"
                    )
                    if found:
                        for k, v in found.items():
                            if "csrf" in k.lower():
                                csrf = v
                                break
            except Exception:
                pass

        if not csrf:
            for c in merged:
                if c.get("name") == "login_aliyunid_csrf":
                    csrf = c.get("value", "")
                    break

        cookies_dict = {c["name"]: c["value"] for c in merged}
        session = {
            "url": driver.current_url,
            "user_agent": driver.execute_script("return navigator.userAgent;"),
            "csrf": csrf,
            "cookies": cookies_dict,
            "cookie_domains": sorted({c.get("domain", "") for c in merged}),
            "saved_at": time.time(),
        }
        SESSION_FILE.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[+] Session 已保存: {SESSION_FILE} (cookies={len(cookies_dict)}, csrf={csrf[:20]!r})")
        return session
    except Exception as e:
        print(f"[!] 保存 session 失败: {e}")
        return None


def capture_xhr_csrf(driver) -> str:
    """从 performance log 偷页面 axios 自动加的 x-csrf-token。"""
    try:
        for entry in driver.get_log("performance"):
            try:
                msg = json.loads(entry["message"])["message"]
            except Exception:
                continue
            if msg.get("method") != "Network.requestWillBeSent":
                continue
            req = msg.get("params", {}).get("request", {})
            url = req.get("url", "")
            if "console.aliyun.com" not in url or "/console/" not in url:
                continue
            for k, v in req.get("headers", {}).items():
                if k.lower() == "x-csrf-token" and v:
                    print(f"[+] 从 XHR 抓到真实 x-csrf-token: {v!r} (来自 {url[:80]})")
                    return v
    except Exception as e:
        print(f"[!] performance log 读取失败: {e}")
    return ""


def main() -> int:
    creds = load_creds()
    username = creds["username"]
    password = creds["password"]
    mfa_secret = creds["mfa_secret"]
    target_url = creds["target_url"]
    project = creds.get("project", "")
    logstore = creds.get("logstore", "")
    default_query = creds.get("default_query", "*")

    callback_enc = quote(target_url, safe="")
    login_url = f"https://signin.aliyun.com/{username.split('@')[1]}/login.htm?callback={callback_enc}#/main"

    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--keep", action="store_true", default=True)
    args = parser.parse_args()

    options = Options()
    if args.headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )

    try:
        print(f"[*] 打开登录页")
        driver.get(login_url)
        wait = WebDriverWait(driver, 20)

        # 1. 账号
        print("[*] 输入账号")
        user_el = find_first(driver, SELECTORS["username"], timeout=12)
        if not user_el:
            print("[!] 未找到账号输入框, 请人工完成登录。")
            _pause_forever()
            return 1
        human_type(user_el, username)

        # 2. 密码 (单页直接命中; 双步模式按 Enter 后再找)
        print("[*] 输入密码")
        pwd_el = find_first(driver, SELECTORS["password"], timeout=2)
        if not pwd_el:
            user_el.send_keys(Keys.ENTER)
            pwd_el = find_first(driver, SELECTORS["password"], timeout=8)
        if not pwd_el:
            print("[!] 仍未找到密码框, 请人工完成登录。")
            _pause_forever()
            return 1
        human_type(pwd_el, password)

        # 3. 提交
        btn = find_first(driver, SELECTORS["submit"], timeout=5) or \
            find_button_by_text(driver, BUTTON_TEXT["submit"], timeout=5)
        if btn:
            btn.click()
        else:
            pwd_el.send_keys(Keys.ENTER)

        # 4. MFA 自动填
        mfa_filled = False
        try:
            mfa_el = find_first(driver, SELECTORS["mfa_code"], timeout=25)
            if mfa_el:
                code = pyotp.TOTP(mfa_secret).now()
                if 30 - int(time.time()) % 30 < 3:
                    time.sleep(3)
                    code = pyotp.TOTP(mfa_secret).now()
                print(f"[+] 生成 MFA 码: {code} (有效 {30 - int(time.time()) % 30}s)")

                def _type(el, c=code):
                    el.click()
                    el.send_keys(c)
                    return el.get_attribute("value") or ""

                entered = with_element(driver, SELECTORS["mfa_code"], _type, attempts=6)
                print(f"[*] 输入 value = {entered!r}")
                time.sleep(0.6)

                if entered != code:
                    def _js_set(el, c=code):
                        driver.execute_script(
                            "const el=arguments[0],v=arguments[1];"
                            "const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                            "s.call(el,v);"
                            "el.dispatchEvent(new Event('input',{bubbles:true}));"
                            "el.dispatchEvent(new Event('change',{bubbles:true}));"
                            "el.dispatchEvent(new KeyboardEvent('keyup',{bubbles:true}));",
                            el, c,
                        )
                        return el.get_attribute("value") or ""

                    entered = with_element(driver, SELECTORS["mfa_code"], _js_set)
                    print(f"[*] JS 兜底后 value = {entered!r}")
                    time.sleep(1.0)

                ok = find_first(driver, SELECTORS["mfa_submit"], timeout=5) or \
                    find_button_by_text(driver, BUTTON_TEXT["mfa_submit"], timeout=3)
                if ok and ok.is_enabled():
                    try:
                        ok.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", ok)
                    mfa_filled = True
                    print("[*] MFA 已提交")
                elif ok and not ok.is_enabled():
                    print("[!] 提交按钮仍 disabled")
                else:
                    print("[!] 未找到提交按钮")
        except Exception as e:
            print(f"[!] MFA 自动填充失败 ({e}), 请人工输入")

        # 5. 跳过 '重置密码'
        try:
            time.sleep(0.8)
            skip = find_first(driver, SELECTORS["skip_reset_css"], timeout=1) or \
                find_button_by_text(driver, BUTTON_TEXT["skip_reset"], timeout=8)
            if skip:
                print("[*] 检测到重置密码提示, 点击跳过")
                try:
                    skip.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", skip)
                time.sleep(1.0)
        except Exception as e:
            print(f"[!] 跳过密码重置失败 ({e})")

        # 6. 等待跳转
        def _landed(d):
            host = urlparse(d.current_url).netloc.lower()
            return (
                host in ("sls.console.aliyun.com", "www.aliyun.com", "console.aliyun.com")
                or host.endswith(".console.aliyun.com")
                or "session.htm" in d.current_url.lower()
            )

        try:
            wait.until(_landed)
            print(f"[+] 登录成功! URL: {driver.current_url}")
        except Exception:
            print(f"[*] 60s 内未检测到跳转, URL: {driver.current_url}")

        # 兜底: 主动跳到目标页
        if urlparse(driver.current_url).netloc != "sls.console.aliyun.com":
            print("[*] 主动跳转到 SLS 目标页")
            driver.get(target_url)
            time.sleep(2.0)

        # 抓 session
        dump_session(driver)
        xhr_csrf = capture_xhr_csrf(driver)
        if xhr_csrf and SESSION_FILE.exists():
            sess = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            sess["csrf"] = xhr_csrf
            SESSION_FILE.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
            print("[+] Session 文件 csrf 已更新为 XHR 真实值")

        # 验证 session 能用 (页面 fetch + 真实 csrf)
        try:
            test = driver.execute_async_script(
                """
                const cb=arguments[arguments.length-1], csrf=arguments[0];
                const p = arguments[1] || 'x', l = arguments[2] || 'x', q = arguments[3] || '*';
                const body = new URLSearchParams({
                    ProjectName: p, LogStoreName: l,
                    from: String(Math.floor(Date.now()/1000)-300),
                    to: String(Math.floor(Date.now()/1000)),
                    query: q,
                    Page:'1', Size:'3', Reverse:'true',
                    pSql:'false', fullComplete:'false', schemaFree:'false', needHighlight:'true',
                });
                const h = {'content-type':'application/x-www-form-urlencoded'};
                if (csrf) h['x-csrf-token'] = csrf;
                fetch('/console/logs/getLogs.json',{method:'POST',credentials:'include',headers:h,body:body.toString()})
                    .then(async r=>cb({status:r.status,body:(await r.text()).slice(0,400)}))
                    .catch(e=>cb({error:String(e)}));
                """,
                xhr_csrf, project, logstore, default_query,
            )
            print(f"[*] 页面 fetch 验证: {test}")
        except Exception as e:
            print(f"[!] 页面 fetch 失败 ({e})")

        if args.keep:
            print("[*] 浏览器窗口保留打开, 按 Ctrl+C 关闭")
            while True:
                time.sleep(60)
    except KeyboardInterrupt:
        print("\n[*] 用户中断")
    finally:
        try:
            if not args.keep:
                driver.quit()
        except Exception:
            pass
    return 0


def _pause_forever() -> None:
    print("[*] 浏览器窗口保留打开, 请人工完成登录。完成后 Ctrl+C 退出")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
