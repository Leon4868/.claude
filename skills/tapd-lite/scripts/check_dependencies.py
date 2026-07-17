#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check and install dependencies."""

import sys
import io
import subprocess
import importlib.util

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def check_dependency(package_name, import_name=None):
    """Check if a package is installed.

    Args:
        package_name: Package name for pip install
        import_name: Import name (if different from package_name)

    Returns:
        True if installed, False otherwise
    """
    if import_name is None:
        import_name = package_name

    spec = importlib.util.find_spec(import_name)
    return spec is not None


def install_dependency(package_name):
    """Install a package using pip.

    Args:
        package_name: Package name to install

    Returns:
        True if successful, False otherwise
    """
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_all_dependencies(auto_install=False):
    """Check all required dependencies.

    Args:
        auto_install: If True, automatically install missing dependencies

    Returns:
        Tuple of (all_installed, missing_packages)
    """
    dependencies = [
        ("pyyaml", "yaml"),
    ]

    missing = []
    for package_name, import_name in dependencies:
        if not check_dependency(package_name, import_name):
            missing.append(package_name)

    if missing and auto_install:
        print("Installing missing dependencies...")
        for package in missing:
            print(f"  Installing {package}...", end=" ")
            if install_dependency(package):
                print("✓")
                missing.remove(package)
            else:
                print("✗")

    return len(missing) == 0, missing


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Check dependencies')
    parser.add_argument('--install', action='store_true',
                       help='Automatically install missing dependencies')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress output')

    args = parser.parse_args()

    all_installed, missing = check_all_dependencies(auto_install=args.install)

    if not args.quiet:
        if all_installed:
            print("✓ All dependencies are installed")
            sys.exit(0)
        else:
            print("✗ Missing dependencies:")
            for package in missing:
                print(f"  - {package}")
            print("\nTo install missing dependencies, run:")
            print(f"  python {__file__} --install")
            print("\nOr manually install with:")
            print(f"  pip install {' '.join(missing)}")
            sys.exit(1)
    else:
        sys.exit(0 if all_installed else 1)


if __name__ == '__main__':
    main()
