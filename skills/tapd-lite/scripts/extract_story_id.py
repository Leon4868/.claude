#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract story ID from Git branch name."""

import argparse
import re
import subprocess
import sys


def get_current_branch():
    """Get current Git branch name.

    Returns:
        Branch name or None if not in a Git repository
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def extract_story_id_from_branch(branch_name):
    """Extract story ID from branch name.

    Supports formats:
    - username/feature/1009034_story_name
    - feature/1009034_story_name
    - 1009034_story_name
    - 1009034-story-name

    Args:
        branch_name: Git branch name

    Returns:
        Tuple of (short_id, full_id) or (None, None) if not found
    """
    # Pattern 1: Extract 7-digit ID from branch name
    # Matches: lwk/feature/1009034_xxx or feature/1009034_xxx
    pattern1 = r'/(\d{7})_'
    match = re.search(pattern1, branch_name)
    if match:
        short_id = match.group(1)
        # Reconstruct full ID (assuming workspace prefix)
        full_id = f"1135238004001{short_id}"
        return short_id, full_id

    # Pattern 2: Extract 7-digit ID at start or after slash
    # Matches: 1009034_xxx or feature/1009034_xxx
    pattern2 = r'(?:^|/)(\d{7})[-_]'
    match = re.search(pattern2, branch_name)
    if match:
        short_id = match.group(1)
        full_id = f"1135238004001{short_id}"
        return short_id, full_id

    # Pattern 3: Extract any 7+ digit number
    pattern3 = r'(\d{7,})'
    match = re.search(pattern3, branch_name)
    if match:
        number = match.group(1)
        if len(number) == 7:
            short_id = number
            full_id = f"1135238004001{short_id}"
            return short_id, full_id
        elif len(number) > 7:
            # Assume it's a full ID
            full_id = number
            short_id = number[-7:]
            return short_id, full_id

    return None, None


def main():
    parser = argparse.ArgumentParser(description='Extract story ID from Git branch')
    parser.add_argument('--branch', help='Branch name (default: current branch)')
    parser.add_argument('--workspace-prefix', default='1135238004001',
                       help='Workspace prefix for full ID (default: 1135238004001)')

    args = parser.parse_args()

    # Get branch name
    if args.branch:
        branch_name = args.branch
    else:
        branch_name = get_current_branch()
        if not branch_name:
            print("ERROR=Not in a Git repository")
            sys.exit(1)

    # Extract story ID
    short_id, full_id = extract_story_id_from_branch(branch_name)

    if short_id:
        print(f"BRANCH_NAME={branch_name}")
        print(f"SHORT_ID={short_id}")
        print(f"FULL_ID={full_id}")
        print(f"SUCCESS=true")
    else:
        print(f"BRANCH_NAME={branch_name}")
        print("ERROR=No story ID found in branch name")
        print("SUCCESS=false")
        sys.exit(1)


if __name__ == '__main__':
    main()
