#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create development branch after confirming involved projects."""

import argparse
import sys
import io
from pathlib import Path

# Set stdout to UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.git_helper import get_git_helper
from core.requirement_doc_manager import get_requirement_doc_manager


def create_branch_from_current_story() -> dict:
    """Create branch for current story (from git branch name or requirement dir).

    Returns:
        Dictionary with operation results

    Raises:
        Exception: If branch creation fails
    """
    results = {
        "story_id": None,
        "branch_name": None,
        "branch_created": False,
    }

    print("🌿 Creating development branch...")
    print("=" * 80)

    # Try to get story ID from current branch
    git_helper = get_git_helper()
    current_branch = git_helper.get_current_branch()

    # Extract story ID from branch name (format: lwk/feature_xxx_<story_id>_<date>)
    story_id = None
    if "_" in current_branch:
        parts = current_branch.split("_")
        if len(parts) >= 3:
            # Try to find story ID (long number)
            for part in parts:
                if part.isdigit() and len(part) > 10:
                    story_id = part
                    break

    if not story_id:
        print("✗ Cannot extract story ID from current branch")
        print(f"  Current branch: {current_branch}")
        print("\n💡 Please provide story ID manually")
        return results

    results["story_id"] = story_id
    print(f"✓ Story ID: {story_id}")

    # Get requirement directory
    doc_manager = get_requirement_doc_manager()
    req_dir = doc_manager.get_requirement_dir(story_id)

    if not req_dir:
        print(f"✗ Requirement directory not found for story: {story_id}")
        return results

    print(f"✓ Requirement dir: {req_dir}")

    # Read development.md to get branch name
    dev_doc_path = req_dir / "development.md"
    if not dev_doc_path.exists():
        print(f"✗ development.md not found: {dev_doc_path}")
        return results

    # Parse branch name from development.md
    branch_name = None
    with open(dev_doc_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("**建议分支名**:"):
                # Extract branch name from markdown code block
                branch_name = line.split("`")[1] if "`" in line else None
                break

    if not branch_name:
        print("✗ Cannot find branch name in development.md")
        return results

    results["branch_name"] = branch_name
    print(f"✓ Branch name: {branch_name}")

    # Create branch
    try:
        git_helper.create_branch(branch_name)
        results["branch_created"] = True
        print(f"✓ Branch created and checked out: {branch_name}")
    except Exception as e:
        print(f"✗ Failed to create branch: {e}")
        raise

    print("\n" + "=" * 80)
    print("✅ Branch created successfully!")
    print(f"\n🌿 Branch: {branch_name}")
    print("\n💡 Next steps:")
    print("  1. Start coding")
    print("  2. Use /commit-cn to commit changes")

    return results


def create_branch_by_story_id(story_id: str) -> dict:
    """Create branch for specific story ID.

    Args:
        story_id: TAPD story ID

    Returns:
        Dictionary with operation results

    Raises:
        Exception: If branch creation fails
    """
    results = {
        "story_id": story_id,
        "branch_name": None,
        "branch_created": False,
    }

    print(f"🌿 Creating development branch for story: {story_id}")
    print("=" * 80)

    # Get requirement directory
    doc_manager = get_requirement_doc_manager()
    req_dir = doc_manager.get_requirement_dir(story_id)

    if not req_dir:
        print(f"✗ Requirement directory not found for story: {story_id}")
        print("\n💡 Please run '/tapd start' first to create requirement documents")
        return results

    print(f"✓ Requirement dir: {req_dir}")

    # Read development.md to get branch name
    dev_doc_path = req_dir / "development.md"
    if not dev_doc_path.exists():
        print(f"✗ development.md not found: {dev_doc_path}")
        return results

    # Parse branch name from development.md
    branch_name = None
    with open(dev_doc_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("**建议分支名**:"):
                # Extract branch name from markdown code block
                branch_name = line.split("`")[1] if "`" in line else None
                break

    if not branch_name:
        print("✗ Cannot find branch name in development.md")
        return results

    results["branch_name"] = branch_name
    print(f"✓ Branch name: {branch_name}")

    # Create branch
    git_helper = get_git_helper()
    try:
        git_helper.create_branch(branch_name)
        results["branch_created"] = True
        print(f"✓ Branch created and checked out: {branch_name}")
    except Exception as e:
        print(f"✗ Failed to create branch: {e}")
        raise

    print("\n" + "=" * 80)
    print("✅ Branch created successfully!")
    print(f"\n🌿 Branch: {branch_name}")
    print("\n💡 Next steps:")
    print("  1. Start coding")
    print("  2. Use /commit-cn to commit changes")

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create development branch for TAPD story",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create branch for current story (auto-detect from branch or requirement dir)
  python create_branch.py

  # Create branch for specific story ID
  python create_branch.py --story-id 1135238004001009034
        """,
    )
    parser.add_argument(
        "--story-id",
        help="TAPD story ID (optional, will auto-detect if not provided)",
    )

    args = parser.parse_args()

    try:
        if args.story_id:
            create_branch_by_story_id(args.story_id)
        else:
            create_branch_from_current_story()
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
