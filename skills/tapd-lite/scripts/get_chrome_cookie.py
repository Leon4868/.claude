#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract TAPD cookies from Chrome browser on Windows."""

import json
import os
import shutil
import sqlite3
import sys
import io
import base64
import tempfile
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_chrome_user_data_dir():
    """Get Chrome user data directory."""
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if not local_app_data:
        # Fallback for environments where LOCALAPPDATA is not set
        home = Path.home()
        local_app_data = str(home / "AppData" / "Local")
    return Path(local_app_data) / "Google" / "Chrome" / "User Data"


def get_encryption_key():
    """Get Chrome's cookie encryption key using DPAPI."""
    try:
        import ctypes
        import ctypes.wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', ctypes.wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_char)),
            ]

        local_state_path = get_chrome_user_data_dir() / "Local State"
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        # Remove "DPAPI" prefix (first 5 bytes)
        encrypted_key = encrypted_key[5:]

        # Decrypt using Windows DPAPI
        input_blob = DATA_BLOB(len(encrypted_key),
                               ctypes.cast(ctypes.create_string_buffer(encrypted_key, len(encrypted_key)),
                                           ctypes.POINTER(ctypes.c_char)))
        output_blob = DATA_BLOB()

        result = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(input_blob), None, None, None, None, 0,
            ctypes.byref(output_blob)
        )

        if not result:
            raise RuntimeError("CryptUnprotectData failed")

        key = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)
        return key

    except Exception as e:
        raise RuntimeError(f"Failed to get encryption key: {e}")


def decrypt_cookie_value(encrypted_value, key):
    """Decrypt a Chrome cookie value."""
    try:
        # Chrome 80+ uses AES-256-GCM with "v10" prefix
        if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
            # v10/v11: AES-256-GCM
            nonce = encrypted_value[3:15]  # 12 bytes nonce
            ciphertext = encrypted_value[15:]

            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted.decode('utf-8', errors='replace')
        else:
            # Old format: DPAPI encrypted
            import ctypes
            import ctypes.wintypes

            class DATA_BLOB(ctypes.Structure):
                _fields_ = [
                    ('cbData', ctypes.wintypes.DWORD),
                    ('pbData', ctypes.POINTER(ctypes.c_char)),
                ]

            input_blob = DATA_BLOB(len(encrypted_value),
                                   ctypes.cast(ctypes.create_string_buffer(encrypted_value, len(encrypted_value)),
                                               ctypes.POINTER(ctypes.c_char)))
            output_blob = DATA_BLOB()
            ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(input_blob), None, None, None, None, 0,
                ctypes.byref(output_blob)
            )
            value = ctypes.string_at(output_blob.pbData, output_blob.cbData)
            ctypes.windll.kernel32.LocalFree(output_blob.pbData)
            return value.decode('utf-8', errors='replace')
    except Exception as e:
        return ""


def get_tapd_cookies():
    """Extract TAPD cookies from Chrome."""
    # Try different cookie database paths (Default + all Profile dirs)
    user_data_dir = get_chrome_user_data_dir()
    profile_dirs = ["Default"]
    # Add Profile 1, Profile 2, ... etc
    if user_data_dir.exists():
        for d in sorted(user_data_dir.iterdir()):
            if d.is_dir() and d.name.startswith("Profile"):
                profile_dirs.append(d.name)

    cookie_paths = []
    for profile in profile_dirs:
        cookie_paths.append(user_data_dir / profile / "Network" / "Cookies")
        cookie_paths.append(user_data_dir / profile / "Cookies")

    cookie_dbs = [path for path in cookie_paths if path.exists()]

    if not cookie_dbs:
        raise FileNotFoundError("Chrome cookie database not found")

    # Get encryption key
    key = get_encryption_key()

    # Try each cookie database until we find TAPD cookies
    for cookie_db in cookie_dbs:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
        os.close(tmp_fd)
        try:
            try:
                shutil.copy2(cookie_db, tmp_path)
            except (PermissionError, OSError):
                try:
                    with open(cookie_db, 'rb') as src:
                        with open(tmp_path, 'wb') as dst:
                            dst.write(src.read())
                except (PermissionError, OSError):
                    # Chrome has exclusive lock on this file
                    continue

            conn = sqlite3.connect(tmp_path)
            conn.execute("PRAGMA journal_mode=wal")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%tapd.cn%'"
            )

            cookies = []
            for name, encrypted_value in cursor.fetchall():
                if encrypted_value:
                    value = decrypt_cookie_value(encrypted_value, key)
                    if value:
                        cookies.append(f"{name}={value}")

            conn.close()

            if cookies:
                return "; ".join(cookies)
        except Exception:
            pass
        finally:
            os.unlink(tmp_path)

    return ""


def save_to_config(cookie_str):
    """Save cookie to user_config.yaml."""
    import yaml
    config_path = Path(__file__).parent.parent / "config" / "user_config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if "user" not in config:
        config["user"] = {}
    config["user"]["tapd_cookie"] = cookie_str

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def main():
    # Manual mode: accept cookie string directly
    if "--manual" in sys.argv:
        idx = sys.argv.index("--manual")
        if idx + 1 < len(sys.argv):
            cookie_str = sys.argv[idx + 1]
            save_to_config(cookie_str)
            cookie_count = len(cookie_str.split("; "))
            print(f"SUCCESS=true")
            print(f"COOKIE_COUNT={cookie_count}")
            print(f"SAVED=true")
            return
        else:
            print("ERROR=--manual requires a cookie string argument")
            sys.exit(1)

    try:
        cookie_str = get_tapd_cookies()
        if not cookie_str:
            print("ERROR=No TAPD cookies found. Possible causes:")
            print("HINT_1=Chrome is running and has locked the cookie database. Please close Chrome completely and retry.")
            print("HINT_2=You have not logged into TAPD (www.tapd.cn) in Chrome.")
            print("HINT_3=Chrome 127+ uses App-Bound Encryption (v20) which cannot be auto-decrypted. Use --manual mode instead.")
            sys.exit(1)

        # Count cookie entries
        cookie_count = len(cookie_str.split("; "))

        if "--save" in sys.argv:
            save_to_config(cookie_str)
            print(f"SUCCESS=true")
            print(f"COOKIE_COUNT={cookie_count}")
            print(f"SAVED=true")
        else:
            print(f"SUCCESS=true")
            print(f"COOKIE_COUNT={cookie_count}")
            print(f"COOKIE={cookie_str}")

    except Exception as e:
        print(f"ERROR={e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
