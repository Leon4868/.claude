"""Archery 自动登录 + session 抓取脚本。

用法:
    python archery_login.py

凭证从 ~/.archery-credentials.json 读取, 不进 git。

流程:
1. Selenium 打开 Chrome, 自动填账号/密码到 archery-k8s.94ai.pro
2. 如果启用 2FA, TOTP 自动算 6 位 MFA 码并填入
3. 跳到 /sqlquery/ 主页
4. 抓 cookies (csrftoken + sessionid) 写到 ~/.archery_session.json
   archery_query.py 优先读这个文件, 无需再配环境变量。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pyotp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

CRED_FILE = Path.home() / ".archery-credentials.json"
SESSION_FILE = Path.home() / ".archery_session.json"


def load_creds() -> dict:
    if not CRED_FILE.exists():
        sys.exit(
            f"[!] 凭证文件不存在: {CRED_FILE}\n"
            "请创建如下格式的 JSON:\n"
            "{\n"
            '  "username": "lianwukun",\n'
            '  "password": "xxx",\n'
            '  "mfa_secret": "BASE32_TOTP_SEED",\n'
            '  "base_url": "https://archery-k8s.94ai.pro",\n'
            '  "login_path": "/login/",\n'
            '  "target_url": "https://archery-k8s.94ai.pro/sqlquery/"\n'
            "}"
        )
    return json.loads(CRED_FILE.read_text(encoding="utf-8"))


# Archery (Django) 登录页 selector, 多 fallback 兜底
SELECTORS = {
    "username": [
        "input#id_username",
        "input[name='username']",
        "input#username",
        "input[placeholder*='用户' i]",
        "input[placeholder*='account' i]",
        "input[type='text']:not([name='csrfmiddlewaretoken'])",
    ],
    "password": [
        "input#id_password",
        "input[name='password']",
        "input#password",
        "input[type='password']",
    ],
    "submit": [
        "button[type='submit']",
        "button.login-btn",
        "button.btn-primary",
        "input[type='submit']",
        "button.fui-btn-primary",
    ],
    # django-two-factor-auth / django-otp 的 6 位 token 输入框
    "mfa_code": [
        "input[name='token-otp_token']",
        "input[name='otp_token']",
        "input[name='token']",
        "input#id_token-otp_token",
        "input#id_otp_token",
        "input[autocomplete='one-time-code']",
        "input[inputmode='numeric']",
        "input[placeholder*='6 位' i]",
        "input[placeholder*='安全码' i]",
        "input[placeholder*='Authenticator' i]",
        "input[placeholder*='verification' i]",
        "input[name*='otp' i]",
    ],
    "mfa_submit": [
        "button#btnAuth",                       # Archery 2FA "验证" 按钮
        "button.btn-success",
        "button.btn-primary:not([style*='display: none'])",
        "button[type='submit']",
        "input[type='submit']",
    ],
}

BUTTON_TEXT = {
    "submit": ["登录", "Login", "Sign in", "下一步", "Next"],
    "mfa_submit": ["提交", "验证", "Verify", "Confirm", "确定"],
}


def find_first(driver, selectors, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for sel in selectors:
            try:
                for el in driver.find_elements(By.CSS_SELECTOR, sel):
                    try:
                        if el.is_displayed() and el.is_enabled():
                            return el
                    except Exception:
                        continue
            except Exception:
                continue
        time.sleep(0.4)
    return None


def find_button_by_text(driver, texts, timeout=8):
    end = time.time() + timeout
    while time.time() < end:
        for t in texts:
            for tag in ("button", "a", "input", "span", "div"):
                try:
                    els = driver.find_elements(
                        By.XPATH,
                        f"//{tag}[contains(normalize-space(string(.)),'{t}')]",
                    )
                    for el in els:
                        try:
                            if not (el.is_displayed() and el.is_enabled()):
                                continue
                        except Exception:
                            continue
                        if tag in ("button", "a", "input"):
                            return el
                        parent = el.find_element(By.XPATH, "..").tag_name
                        if parent in ("button", "a"):
                            return el
                except Exception:
                    continue
        time.sleep(0.4)
    return None


def with_element(driver, selectors, action, attempts=12, delay=0.4):
    """每次重试都重新查找元素, 防止页面重渲染导致 stale。"""
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


def dump_session(driver, base_url: str) -> dict | None:
    """抓所有域 cookies + csrf, 写到 SESSION_FILE。

    输出格式与 archery_query.py 兼容:
      - cookie: "k1=v1; k2=v2" 形式 (兼容老的 ARCHERY_COOKIE 环境变量)
      - cookies_dict: dict 形式 (供 requests 直接用)
      - csrf_token: 取 cookie 里的 csrftoken (Django 模式)
    """
    try:
        time.sleep(1.5)
        all_cookies = driver.execute_cdp_cmd("Network.getAllCookies", {}).get("cookies", [])
        all_cookies.extend(driver.get_cookies())
        seen, merged = set(), []
        for c in all_cookies:
            key = (c.get("name"), c.get("domain"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(c)

        cookies_dict = {c["name"]: c["value"] for c in merged}
        csrf = cookies_dict.get("csrftoken", "")

        # 兜底: meta 标签 / form 里的 csrfmiddlewaretoken
        if not csrf:
            try:
                csrf = driver.execute_script(
                    """
                    const m = document.querySelector('meta[name="csrf-token"]');
                    if (m) return m.content;
                    const i = document.querySelector('input[name="csrfmiddlewaretoken"]');
                    if (i) return i.value;
                    return '';
                    """
                ) or ""
            except Exception:
                pass

        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())
        session = {
            "base_url": base_url.rstrip("/"),
            "csrf_token": csrf,
            "cookie": cookie_str,
            "cookies_dict": cookies_dict,
            "user_agent": driver.execute_script("return navigator.userAgent;"),
            "url": driver.current_url,
            "saved_at": time.time(),
        }
        SESSION_FILE.write_text(
            json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            f"[+] Session 已保存: {SESSION_FILE} "
            f"(cookies={len(cookies_dict)}, csrftoken={csrf[:12]!r})"
        )
        return session
    except Exception as e:
        print(f"[!] 保存 session 失败: {e}")
        return None


def is_logged_in(driver, base_url: str) -> bool:
    """判断是否已登录: 不在 /login/ 路径, 且有 sessionid cookie。"""
    host = urlparse(driver.current_url).netloc
    path = urlparse(driver.current_url).path.lower()
    base_host = urlparse(base_url).netloc
    if host != base_host:
        return False
    if path.startswith("/login"):
        return False
    cookies = {c.get("name"): c.get("value") for c in driver.get_cookies()}
    return bool(cookies.get("sessionid"))


def main() -> int:
    creds = load_creds()
    username = creds["username"]
    password = creds["password"]
    mfa_secret = creds["mfa_secret"]
    base_url = creds.get("base_url", "https://archery-k8s.94ai.pro").rstrip("/")
    login_path = creds.get("login_path", "/login/")
    target_url = creds.get("target_url", f"{base_url}/sqlquery/")
    login_url = f"{base_url}{login_path}"

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
        print(f"[*] 打开 Archery 登录页: {login_url}")
        driver.get(login_url)
        _ = WebDriverWait(driver, 20)

        # 已登录直接跳过
        if is_logged_in(driver, base_url):
            print("[+] 检测到已登录 (浏览器缓存), 直接抓 session")
            driver.get(target_url)
            time.sleep(1.5)
            dump_session(driver, base_url)
            return 0

        # 1. 账号
        print("[*] 输入账号")
        user_el = find_first(driver, SELECTORS["username"], timeout=15)
        if not user_el:
            print("[!] 未找到账号输入框, 请人工完成登录。")
            _pause_forever()
            return 1
        human_type(user_el, username)

        # 2. 密码
        print("[*] 输入密码")
        pwd_el = find_first(driver, SELECTORS["password"], timeout=5)
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
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
        else:
            pwd_el.send_keys(Keys.ENTER)
        print("[*] 已提交登录表单")

        # 4. MFA 自动填 (如果启用 2FA)
        time.sleep(1.5)
        mfa_el = find_first(driver, SELECTORS["mfa_code"], timeout=6)
        if mfa_el:
            print("[*] 检测到 MFA 输入框, 自动填 TOTP")
            try:
                # 等 30s 窗口剩 >=5s, 避免 TOTP 在提交瞬间过期
                remain = 30 - int(time.time()) % 30
                if remain < 5:
                    time.sleep(remain + 1)
                code = pyotp.TOTP(mfa_secret).now()
                remain = 30 - int(time.time()) % 30
                print(f"[+] 生成 MFA 码: {code} (有效 {remain}s)")

                # 永远先走 JS dispatchEvent 兜底, 触发 React/Vue onChange
                # (单纯 send_keys 在现代前端框架里经常不触发 disabled→enabled 切换)
                def _js_set(el, c=code):
                    driver.execute_script(
                        "const el=arguments[0],v=arguments[1];"
                        "const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                        "s.call(el,v);"
                        "el.dispatchEvent(new Event('input',{bubbles:true}));"
                        "el.dispatchEvent(new Event('change',{bubbles:true}));"
                        "el.dispatchEvent(new KeyboardEvent('keyup',{bubbles:true}));"
                        "el.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'0'}));"
                        "el.dispatchEvent(new Event('blur',{bubbles:true}));",
                        el, c,
                    )
                    return el.get_attribute("value") or ""

                entered = with_element(driver, SELECTORS["mfa_code"], _js_set, attempts=6)
                print(f"[*] JS 填入 value = {entered!r}")
                time.sleep(1.0)

                # 兜底: JS 仍没填进 value 才用 send_keys
                if entered != code:
                    def _type(el, c=code):
                        el.click()
                        el.send_keys(c)
                        return el.get_attribute("value") or ""

                    entered = with_element(driver, SELECTORS["mfa_code"], _type, attempts=4)
                    print(f"[*] send_keys 兜底 value = {entered!r}")
                    time.sleep(0.8)

                # 多次轮询找 submit 按钮, 等 disabled→enabled
                ok = None
                wait_end = time.time() + 15
                while time.time() < wait_end:
                    ok = find_first(driver, SELECTORS["mfa_submit"], timeout=2) or \
                        find_button_by_text(driver, BUTTON_TEXT["mfa_submit"], timeout=2)
                    if ok:
                        try:
                            if ok.is_enabled() and ok.is_displayed():
                                break
                        except Exception:
                            pass
                    time.sleep(0.8)
                    # 重新触发一次事件, 防止框架需要二次确认
                    with_element(driver, SELECTORS["mfa_code"], _js_set, attempts=2)

                if ok:
                    try:
                        print(f"[*] 提交按钮 id={ok.get_attribute('id')!r} class={ok.get_attribute('class')!r} text={ok.text!r}")
                        ok.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", ok)
                    print("[*] MFA 已提交")
                else:
                    print("[!] 未找到 MFA 提交按钮, 请人工点")
            except Exception as e:
                print(f"[!] MFA 自动填充失败 ({e}), 请人工输入")
        else:
            print("[*] 未检测到 MFA 输入框 (账号可能未启用 2FA, 继续等待跳转)")

        # 5. 等待登录完成 (跳到非 /login/ 路径, 且有 sessionid)
        def _landed(d):
            return is_logged_in(d, base_url)

        try:
            WebDriverWait(driver, 60).until(_landed)
            print(f"[+] 登录成功! URL: {driver.current_url}")
        except Exception:
            print(f"[!] 60s 内未完成登录, 当前 URL: {driver.current_url}")
            print("[!] 请人工完成登录后, 重新跑本脚本抓 session")
            _pause_forever()
            return 1

        # 6. 主动跳到 /sqlquery/ 触发主页加载
        if urlparse(driver.current_url).path.lower().startswith("/login"):
            driver.get(target_url)
            time.sleep(1.5)

        # 7. 抓 session
        dump_session(driver, base_url)

        # 8. 验证 session + 同时 hook XHR 把浏览器自动加的 Cookie header 暴露出来
        #    (selenium 4 performance log 默认 buffer 太小, 经常被前面的 navigation log 挤掉)
        try:
            driver.execute_script(
                """
                window.__xhrLog = [];
                const origOpen = XMLHttpRequest.prototype.open;
                const origSend = XMLHttpRequest.prototype.send;
                const origSetH = XMLHttpRequest.prototype.setRequestHeader;
                XMLHttpRequest.prototype.open = function(m, u) {
                    this.__url = u; this.__method = m; this.__headers = {};
                    return origOpen.apply(this, arguments);
                };
                XMLHttpRequest.prototype.setRequestHeader = function(k, v) {
                    this.__headers[k] = v;
                    return origSetH.apply(this, arguments);
                };
                XMLHttpRequest.prototype.send = function(body) {
                    this.addEventListener('load', () => {
                        try {
                            window.__xhrLog.push({
                                url: this.__url, method: this.__method,
                                status: this.status,
                                headers: this.__headers,
                                // 浏览器在 getAllResponseHeaders 里只暴露非敏感头,
                                // 但 document.cookie 能拿到当前页所有非 HttpOnly cookies
                                cookie_from_js: document.cookie,
                            });
                        } catch(e) {}
                    });
                    return origSend.apply(this, arguments);
                };
                """
            )
            time.sleep(0.3)
            test = driver.execute_async_script(
                """
                const cb=arguments[arguments.length-1], csrf=arguments[0];
                const xhr = new XMLHttpRequest();
                xhr.open('GET', '/group/user_all_instances/?tag_codes%5B%5D=can_read', true);
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                if (csrf) xhr.setRequestHeader('X-CSRFToken', csrf);
                xhr.onload = () => cb({status: xhr.status, body: xhr.responseText.slice(0, 400)});
                xhr.onerror = (e) => cb({error: String(e)});
                xhr.send();
                """,
                cookies_dict_to_dict(driver),
            )
            print(f"[*] 页面 XHR 验证 (list-instances): {test}")
        except Exception as e:
            print(f"[!] 页面 XHR 失败 ({e})")

        # 9. JS hook 抓的 document.cookie (浏览器侧权威)
        real_cookie_header = ""
        try:
            xhr_log = driver.execute_script("return window.__xhrLog || [];")
            if xhr_log:
                last = xhr_log[-1]
                real_cookie_header = last.get("cookie_from_js", "")
                print(f"[*] XHR hook 抓到 {len(xhr_log)} 条 XHR")
                print(f"    最后一条: status={last.get('status')} url={last.get('url','')[:60]}")
                print(f"    document.cookie 长度: {len(real_cookie_header)}")
        except Exception as e:
            print(f"[!] XHR log 读取失败: {e}")

        # 10. document.cookie 是 JS 可见的 (不含 HttpOnly), driver.get_cookies() 含 HttpOnly
        #     Archery 的 sessionid 通常是 HttpOnly, document.cookie 看不到,
        #     但 driver.get_cookies() 能拿到. 如果两者都拿不到的 cookie 就是问题所在
        try:
            doc_cookie = driver.execute_script("return document.cookie;") or ""
            driver_cookies = {c.get("name"): c.get("value") for c in driver.get_cookies()}
            print(f"[*] document.cookie keys: {[kv.split('=',1)[0].strip() for kv in doc_cookie.split(';') if '=' in kv]}")
            print(f"[*] driver.get_cookies() keys: {list(driver_cookies.keys())}")
            for k, v in driver_cookies.items():
                if k.lower() in ("sessionid", "csrftoken", "acw_tc"):
                    print(f"    {k} = {v[:30]}... (len={len(v)})")
        except Exception as e:
            pass

        # 11. 用 driver.get_cookies() 的完整 cookies (含 HttpOnly) 覆盖 session 文件
        #     这是 selenium 能给的最权威版本
        if SESSION_FILE.exists():
            sess = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            driver_cookies_full = {c.get("name"): c.get("value") for c in driver.get_cookies()}
            cookie_str = "; ".join(f"{k}={v}" for k, v in driver_cookies_full.items())
            sess["cookies_dict"] = driver_cookies_full
            sess["cookie"] = cookie_str
            if "csrftoken" in driver_cookies_full and driver_cookies_full["csrftoken"]:
                sess["csrf_token"] = driver_cookies_full["csrftoken"]
            SESSION_FILE.write_text(
                json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"[+] Session 已用 driver.get_cookies() 重新刷新 (keys={list(driver_cookies_full.keys())})")

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


def cookies_dict_to_dict(driver):
    """从当前 driver 拿 csrftoken, 供 fetch 验证用。"""
    try:
        for c in driver.get_cookies():
            if c.get("name") == "csrftoken":
                return c.get("value", "")
    except Exception:
        pass
    return ""


def _pause_forever() -> None:
    print("[*] 浏览器窗口保留打开, 请人工完成登录。完成后 Ctrl+C 退出")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
