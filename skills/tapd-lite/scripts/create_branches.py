#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create branch in multiple Git projects."""

import argparse
import sys
import io
import os
import subprocess
from pathlib import Path
import yaml

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import find_base_branch module
sys.path.insert(0, str(Path(__file__).parent))
try:
    from find_base_branch import find_base_branch as find_base_branch_func
except ImportError:
    find_base_branch_func = None


def load_git_config():
    """Load git configuration."""
    config_path = Path(__file__).parent.parent / "config" / "git_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_base_branch_for_project(project_path):
    """Get base branch for a project using find_base_branch logic.

    Returns:
        Tuple of (base_branch, is_auto_detected)
    """
    if not find_base_branch_func:
        return "develop", False

    try:
        config = load_git_config()
        base_config = config["git"]["base_branch"]
        pattern = base_config.get("pattern")
        sort_by = base_config.get("sort_by", "both")

        base_branch = find_base_branch_func(project_path, pattern, sort_by)
        if base_branch:
            return base_branch, True
        else:
            # Use fallback
            fallback = base_config.get("fallback", "develop")
            return fallback, False
    except Exception:
        return "develop", False


def create_branch(project_path, branch_name, base_branch=None):
    """Create branch in a Git project.

    Args:
        project_path: Path to the Git project
        branch_name: Name of the branch to create
        base_branch: Base branch to create from (None = auto-detect)

    Returns:
        Tuple of (success, message, base_branch_used)
    """
    project_path = Path(project_path)

    if not project_path.exists():
        return False, f"Project not found: {project_path}", None

    if not (project_path / '.git').exists():
        return False, f"Not a Git repository: {project_path}", None

    try:
        # Change to project directory
        original_dir = Path.cwd()
        os.chdir(project_path)

        # Auto-detect base branch if not provided
        if base_branch is None:
            base_branch, is_auto = get_base_branch_for_project(project_path)
            if not is_auto:
                print(f"Warning: Using fallback base branch '{base_branch}' for {project_path.name}", file=sys.stderr)

        # Check if branch already exists
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout.strip():
            return False, f"Branch already exists: {branch_name}", base_branch

        # Fetch latest changes
        subprocess.run(['git', 'fetch', '--all'], capture_output=True, check=False)

        # Create and checkout new branch
        result = subprocess.run(
            ['git', 'checkout', '-b', branch_name, f'origin/{base_branch}'],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            # Try without origin prefix
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name, base_branch],
                capture_output=True,
                text=True,
                check=False
            )

        os.chdir(original_dir)

        if result.returncode == 0:
            return True, f"Branch created successfully from {base_branch}", base_branch
        else:
            return False, f"Failed to create branch: {result.stderr}", base_branch

    except Exception as e:
        return False, f"Error: {e}", None


def main():
    parser = argparse.ArgumentParser(description='Create branch in Git projects')
    parser.add_argument('branch_name', help='Branch name to create')
    parser.add_argument('--projects', nargs='+', required=True, help='Project paths')
    parser.add_argument('--base-branch', help='Base branch (default: auto-detect)')
    parser.add_argument('--show-progress', action='store_true', help='Show progress during execution')

    args = parser.parse_args()

    total = len(args.projects)
    results = []

    for idx, project_path in enumerate(args.projects, 1):
        if args.show_progress:
            print(f"Processing {idx}/{total}: {Path(project_path).name}...", file=sys.stderr)

        success, message, base_used = create_branch(project_path, args.branch_name, args.base_branch)
        results.append({
            'project': Path(project_path).name,
            'path': project_path,
            'success': success,
            'message': message,
            'base_branch': base_used
        })

        if args.show_progress:
            status = "✓" if success else "✗"
            print(f"  {status} {message}", file=sys.stderr)

    # Output results
    print(f"BRANCH_NAME={args.branch_name}")
    print(f"TOTAL_PROJECTS={len(results)}")
    print("RESULTS_START")
    for result in results:
        status = "SUCCESS" if result['success'] else "FAILED"
        base_info = f" (base: {result['base_branch']})" if result['base_branch'] else ""
        print(f"{result['project']}|{status}|{result['message']}{base_info}")
    print("RESULTS_END")

    # Exit with error if any failed
    if any(not r['success'] for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
