#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize user configuration."""

import argparse
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import config_loader


def init_config(tapd_username, git_username_abbr, requirements_dir, tapd_token=None, tapd_cookie=None):
    """Initialize user configuration.

    Args:
        tapd_username: TAPD username
        git_username_abbr: Git username abbreviation
        requirements_dir: Requirements directory path
        tapd_token: TAPD API token (optional)
        tapd_cookie: TAPD browser cookie (optional)

    Returns:
        True if successful
    """
    config = config_loader.load_user_config()

    # Update configuration
    config["user"]["tapd_username"] = tapd_username
    config["user"]["git_username_abbr"] = git_username_abbr
    config["paths"]["requirements_dir"] = requirements_dir

    # Store TAPD token if provided
    if tapd_token:
        config["user"]["tapd_token"] = tapd_token

    # Store TAPD cookie if provided
    if tapd_cookie:
        config["user"]["tapd_cookie"] = tapd_cookie

    config["initialized"] = True

    # Save configuration
    config_loader.save_user_config(config)

    return True


def get_config_value(key):
    """Get configuration value.

    Args:
        key: Configuration key (e.g., 'user.tapd_username', 'paths.requirements_dir')

    Returns:
        Configuration value or None
    """
    config = config_loader.load_user_config()

    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None

    return value
    """Get configuration value.

    Args:
        key: Configuration key (e.g., 'user.tapd_username', 'paths.requirements_dir')

    Returns:
        Configuration value or None
    """
    config = load_user_config()

    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None

    return value


def is_initialized():
    """Check if configuration is initialized."""
    config = load_user_config()
    return config.get("initialized", False)


def main():
    parser = argparse.ArgumentParser(description='Initialize user configuration')
    parser.add_argument('--tapd-username', help='TAPD username')
    parser.add_argument('--git-username-abbr', help='Git username abbreviation')
    parser.add_argument('--requirements-dir', help='Requirements directory path')
    parser.add_argument('--tapd-token', help='TAPD API token')
    parser.add_argument('--tapd-cookie', help='TAPD browser cookie')
    parser.add_argument('--check', action='store_true', help='Check if initialized')
    parser.add_argument('--get', help='Get configuration value')

    args = parser.parse_args()

    if args.check:
        # Check if initialized
        if config_loader.is_initialized():
            config = config_loader.load_user_config()
            print("INITIALIZED=true")
            print(f"TAPD_USERNAME={config['user']['tapd_username']}")
            print(f"GIT_USERNAME_ABBR={config['user']['git_username_abbr']}")
            print(f"REQUIREMENTS_DIR={config['paths']['requirements_dir']}")
            if 'tapd_token' in config['user']:
                print("TAPD_TOKEN=configured")
            if 'tapd_cookie' in config['user']:
                print("TAPD_COOKIE=configured")
        else:
            print("INITIALIZED=false")
            sys.exit(1)

    elif args.get:
        # Get configuration value
        value = get_config_value(args.get)
        if value is not None:
            print(f"{args.get}={value}")
        else:
            print(f"ERROR=Configuration key not found: {args.get}")
            sys.exit(1)

    else:
        # Initialize configuration
        if not args.tapd_username or not args.git_username_abbr or not args.requirements_dir:
            print("ERROR=Missing required arguments")
            print("Usage: init_config.py --tapd-username <name> --git-username-abbr <abbr> --requirements-dir <dir> [--tapd-token <token>] [--tapd-cookie <cookie>]")
            sys.exit(1)

        try:
            init_config(args.tapd_username, args.git_username_abbr, args.requirements_dir, args.tapd_token, args.tapd_cookie)
            print("SUCCESS=true")
            print(f"TAPD_USERNAME={args.tapd_username}")
            print(f"GIT_USERNAME_ABBR={args.git_username_abbr}")
            print(f"REQUIREMENTS_DIR={args.requirements_dir}")
            if args.tapd_token:
                print("TAPD_TOKEN=configured")
            if args.tapd_cookie:
                print("TAPD_COOKIE=configured")

            # Run verification after initialization
            print("\nVerifying configuration...")
            from verify_config import verify_user_config, verify_tapd_token

            success, message = verify_user_config()
            print(f"User Config: {'✓' if success else '✗'} {message}")

            success, message = verify_tapd_token()
            print(f"TAPD Token: {'✓' if success else '✗'} {message}")

        except Exception as e:
            print(f"ERROR={str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    main()
