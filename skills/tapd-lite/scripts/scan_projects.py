#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan parent directory for Git projects."""

import argparse
import sys
import io
import os
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def is_git_repo(path):
    """Check if a directory is a Git repository."""
    git_dir = path / '.git'
    return git_dir.exists() and git_dir.is_dir()


def scan_git_projects(base_dir=None):
    """Scan for Git projects in the parent directory.

    Args:
        base_dir: Base directory to scan. If None, uses current directory's parent.

    Returns:
        List of Git project paths
    """
    if base_dir is None:
        # Get parent directory of current working directory
        base_dir = Path.cwd().parent
    else:
        base_dir = Path(base_dir)

    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        sys.exit(1)

    git_projects = []

    # Scan all subdirectories
    for item in base_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if is_git_repo(item):
                git_projects.append(item)

    # Sort by name
    git_projects.sort(key=lambda p: p.name)

    # Output format for Claude to parse
    print(f"BASE_DIR={base_dir}")
    print(f"CURRENT_DIR={Path.cwd()}")
    print(f"CURRENT_PROJECT={Path.cwd().name}")
    print(f"TOTAL_PROJECTS={len(git_projects)}")
    print("PROJECTS_START")
    for project in git_projects:
        print(f"{project.name}|{project}")
    print("PROJECTS_END")

    return git_projects


def main():
    parser = argparse.ArgumentParser(description='Scan for Git projects')
    parser.add_argument('--base-dir', help='Base directory to scan (default: parent of current dir)')

    args = parser.parse_args()

    try:
        scan_git_projects(args.base_dir)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
