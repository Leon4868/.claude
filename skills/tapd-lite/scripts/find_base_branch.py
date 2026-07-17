#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find base branch for creating feature branches."""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import yaml


def load_config():
    """Load git configuration."""
    config_path = Path(__file__).parent.parent / "config" / "git_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["git"]["base_branch"]


def run_git_command(cmd, cwd=None):
    """Run git command and return output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None


def fetch_remote_branches(project_path=None):
    """Fetch remote branches."""
    print("Fetching remote branches...", file=sys.stderr)
    result = run_git_command(["git", "fetch", "--all"], cwd=project_path)
    if result is None:
        print("Warning: Failed to fetch remote branches", file=sys.stderr)
        return False
    return True


def get_all_branches(project_path=None, include_remote=True):
    """Get all branches (local and remote)."""
    if include_remote:
        output = run_git_command(["git", "branch", "-a"], cwd=project_path)
    else:
        output = run_git_command(["git", "branch"], cwd=project_path)

    if not output:
        return []

    branches = []
    for line in output.split('\n'):
        line = line.strip()
        if not line or '->' in line:  # Skip HEAD pointer
            continue
        # Remove * and whitespace
        branch = line.lstrip('* ').strip()
        # Remove remote prefix
        if branch.startswith('remotes/origin/'):
            branch = branch.replace('remotes/origin/', '')
        branches.append(branch)

    # Remove duplicates
    return list(set(branches))


def get_branch_commit_time(branch, project_path=None):
    """Get the last commit time of a branch."""
    cmd = ["git", "log", "-1", "--format=%ct", branch]
    output = run_git_command(cmd, cwd=project_path)
    if output:
        try:
            return int(output)
        except ValueError:
            return 0
    return 0


def find_base_branch(project_path=None, pattern=None, sort_by="both"):
    """Find the base branch matching the pattern.

    Args:
        project_path: Path to git project
        pattern: Regex pattern for branch name
        sort_by: Sorting method - "name", "commit_time", or "both"

    Returns:
        Branch name or None
    """
    # Fetch remote branches first
    fetch_remote_branches(project_path)

    # Get all branches
    branches = get_all_branches(project_path)

    if not branches:
        return None

    # Filter branches by pattern
    if pattern:
        regex = re.compile(pattern)
        matching_branches = [b for b in branches if regex.match(b)]
    else:
        matching_branches = branches

    if not matching_branches:
        return None

    # Sort branches
    if sort_by == "name":
        # Sort by branch name (descending)
        matching_branches.sort(reverse=True)
        return matching_branches[0]

    elif sort_by == "commit_time":
        # Sort by commit time (descending)
        branch_times = [(b, get_branch_commit_time(b, project_path)) for b in matching_branches]
        branch_times.sort(key=lambda x: x[1], reverse=True)
        return branch_times[0][0]

    elif sort_by == "both":
        # Sort by name first, then by commit time if names are equal
        matching_branches.sort(reverse=True)
        # Get the latest by name
        latest_by_name = matching_branches[0]

        # Check if there are multiple branches with the same name pattern
        # (unlikely but handle it)
        same_name_branches = [b for b in matching_branches if b == latest_by_name]

        if len(same_name_branches) > 1:
            # Sort by commit time
            branch_times = [(b, get_branch_commit_time(b, project_path)) for b in same_name_branches]
            branch_times.sort(key=lambda x: x[1], reverse=True)
            return branch_times[0][0]

        return latest_by_name

    return None


def main():
    parser = argparse.ArgumentParser(description='Find base branch for feature branches')
    parser.add_argument('--project-path', help='Path to git project')
    parser.add_argument('--pattern', help='Branch name pattern (regex)')
    parser.add_argument('--sort-by', choices=['name', 'commit_time', 'both'],
                       default='both', help='Sorting method')
    parser.add_argument('--list-all', action='store_true',
                       help='List all matching branches')
    parser.add_argument('--show-fallback', action='store_true',
                       help='Show fallback options if no match found')

    args = parser.parse_args()

    # Load config if pattern not provided
    if not args.pattern:
        config = load_config()
        pattern = config.get("pattern", "^release_20\\d{6}$")
        sort_by = config.get("sort_by", "both")
        fallback = config.get("fallback", "develop")
    else:
        pattern = args.pattern
        sort_by = args.sort_by
        fallback = "develop"

    # Find base branch
    if args.list_all:
        # List all matching branches
        fetch_remote_branches(args.project_path)
        branches = get_all_branches(args.project_path)
        regex = re.compile(pattern)
        matching = [b for b in branches if regex.match(b)]

        if matching:
            print(f"PATTERN={pattern}")
            print(f"TOTAL_BRANCHES={len(matching)}")
            print("BRANCHES_START")
            for branch in sorted(matching, reverse=True):
                commit_time = get_branch_commit_time(branch, args.project_path)
                time_str = datetime.fromtimestamp(commit_time).strftime('%Y-%m-%d %H:%M:%S')
                print(f"{branch}|{commit_time}|{time_str}")
            print("BRANCHES_END")
        else:
            print(f"PATTERN={pattern}")
            print("TOTAL_BRANCHES=0")
            sys.exit(1)
    else:
        # Find the best matching branch
        base_branch = find_base_branch(args.project_path, pattern, sort_by)

        if base_branch:
            commit_time = get_branch_commit_time(base_branch, args.project_path)
            time_str = datetime.fromtimestamp(commit_time).strftime('%Y-%m-%d %H:%M:%S')

            print(f"BASE_BRANCH={base_branch}")
            print(f"COMMIT_TIME={commit_time}")
            print(f"COMMIT_TIME_STR={time_str}")
            print(f"PATTERN={pattern}")
            print(f"SORT_BY={sort_by}")
        else:
            print(f"PATTERN={pattern}")
            print("BASE_BRANCH=")
            print("ERROR=No matching branch found")

            # Show fallback options if requested
            if args.show_fallback:
                print(f"FALLBACK={fallback}")

                # List all branches as alternatives
                fetch_remote_branches(args.project_path)
                branches = get_all_branches(args.project_path)
                if branches:
                    print(f"TOTAL_BRANCHES={len(branches)}")
                    print("ALL_BRANCHES_START")
                    for branch in sorted(branches)[:20]:  # Limit to 20
                        print(branch)
                    print("ALL_BRANCHES_END")

            sys.exit(1)


if __name__ == '__main__':
    main()
