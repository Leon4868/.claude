#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify configuration and test connections."""

import argparse
import sys
import io
import os
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

try:
    from config_loader import config_loader
    from tapd_client import TAPDClient
except ImportError as e:
    print(f"ERROR=Failed to import modules: {e}")
    sys.exit(1)


def verify_user_config():
    """Verify user configuration.

    Returns:
        Tuple of (success, message)
    """
    try:
        if not config_loader.is_initialized():
            return False, "User configuration not initialized. Run 'init_config.py' first."

        config = config_loader.load_user_config()

        # Check required fields
        tapd_username = config.get("user", {}).get("tapd_username")
        git_username_abbr = config.get("user", {}).get("git_username_abbr")
        requirements_dir = config.get("paths", {}).get("requirements_dir")

        if not tapd_username:
            return False, "TAPD username is not set"

        if not git_username_abbr:
            return False, "Git username abbreviation is not set"

        if not requirements_dir:
            return False, "Requirements directory is not set"

        return True, "User configuration is valid"

    except Exception as e:
        return False, f"Failed to load user configuration: {e}"


def verify_tapd_token():
    """Verify TAPD token is set.

    Returns:
        Tuple of (success, message)
    """
    try:
        # First check user config for token
        user_config = config_loader.load_user_config()
        token = user_config.get("user", {}).get("tapd_token")

        if token:
            return True, "TAPD token is set (from config file)"

        # Fallback to environment variable
        tapd_config = config_loader.load_tapd_config()
        token_env = tapd_config["tapd"]["token_env"]
        token = os.getenv(token_env)

        if not token:
            return False, f"TAPD token not found. Set {token_env} environment variable or configure via init_config.py"

        return True, f"TAPD token is set ({token_env})"

    except Exception as e:
        return False, f"Failed to check TAPD token: {e}"


def verify_tapd_connection():
    """Verify TAPD API connection.

    Returns:
        Tuple of (success, message)
    """
    try:
        client = TAPDClient()

        # Try to query stories (with limit 1 to minimize load)
        tapd_username = config_loader.get_tapd_username()
        if not tapd_username:
            return False, "TAPD username not configured"

        stories = client.query_stories(owner=tapd_username, limit=1)

        return True, f"TAPD API connection successful (found {len(stories)} stories)"

    except Exception as e:
        return False, f"TAPD API connection failed: {e}"


def verify_git_config():
    """Verify Git configuration.

    Returns:
        Tuple of (success, message)
    """
    try:
        config = config_loader.load_git_config()

        # Check required fields
        branch_format = config["git"].get("branch_format")
        if not branch_format:
            return False, "Branch format is not set"

        base_branch_config = config["git"].get("base_branch")
        if not base_branch_config:
            return False, "Base branch configuration is not set"

        return True, "Git configuration is valid"

    except Exception as e:
        return False, f"Failed to load Git configuration: {e}"


def verify_requirements_dir():
    """Verify requirements directory.

    Returns:
        Tuple of (success, message)
    """
    try:
        req_dir = config_loader.get_requirements_dir()

        if not req_dir.exists():
            # Try to create it
            req_dir.mkdir(parents=True, exist_ok=True)
            return True, f"Requirements directory created: {req_dir}"
        else:
            return True, f"Requirements directory exists: {req_dir}"

    except Exception as e:
        return False, f"Failed to verify requirements directory: {e}"


def main():
    parser = argparse.ArgumentParser(description='Verify configuration')
    parser.add_argument('--check', choices=['all', 'user', 'tapd', 'git', 'dir'],
                       default='all', help='What to check')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')

    args = parser.parse_args()

    checks = []

    if args.check in ['all', 'user']:
        checks.append(('User Config', verify_user_config))

    if args.check in ['all', 'tapd']:
        checks.append(('TAPD Token', verify_tapd_token))
        checks.append(('TAPD Connection', verify_tapd_connection))

    if args.check in ['all', 'git']:
        checks.append(('Git Config', verify_git_config))

    if args.check in ['all', 'dir']:
        checks.append(('Requirements Dir', verify_requirements_dir))

    # Run checks
    results = []
    all_passed = True

    for name, check_func in checks:
        success, message = check_func()
        results.append((name, success, message))
        if not success:
            all_passed = False

    # Output results
    if args.verbose or not all_passed:
        print("\nConfiguration Verification Results:\n")
        for name, success, message in results:
            status = "✓" if success else "✗"
            print(f"{status} {name}: {message}")
        print()

    # Output machine-readable format
    print(f"ALL_PASSED={all_passed}")
    for name, success, message in results:
        check_name = name.replace(' ', '_').upper()
        print(f"{check_name}_SUCCESS={success}")
        print(f"{check_name}_MESSAGE={message}")

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
