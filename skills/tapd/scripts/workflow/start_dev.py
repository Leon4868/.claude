#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start development workflow - create branch, docs, and update TAPD status."""

import argparse
import sys
import io
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tapd_api import get_tapd_client
from core.git_helper import get_git_helper
from core.requirement_doc_manager import get_requirement_doc_manager
from core.config_manager import get_config_manager


def start_development(story_id: str, date: str = None, force: bool = False) -> dict:
    """Start development for a story.

    Args:
        story_id: TAPD story ID
        date: Date string (YYYYMMDD). Defaults to today.
        force: If True, overwrite existing files without prompting

    Returns:
        Dictionary with operation results

    Raises:
        Exception: If any operation fails
    """
    results = {
        "story": None,
        "branch_name": None,
        "docs_dir": None,
        "docs": {},
        "status_updated": False,
    }

    print(f"🚀 Starting development for story: {story_id}")
    print("=" * 80)

    # 1. Get story details from TAPD
    print("\n📋 Fetching story details from TAPD...")
    tapd_client = get_tapd_client()
    story = tapd_client.get_story_detail(story_id)
    results["story"] = story

    print(f"✓ Story: {story.get('name')}")
    print(f"  Owner: {story.get('owner')}")
    print(f"  Status: {story.get('status')}")
    print(f"  Priority: {story.get('priority')}")

    # 2. Generate branch name (but don't create it yet)
    print("\n🌿 Generating branch name...")
    git_helper = get_git_helper()
    branch_name = git_helper.format_branch_name(
        story_id=story_id,
        story_name=story.get("name", ""),
        date=date,
        version=story.get("version", ""),
    )
    results["branch_name"] = branch_name
    print(f"✓ Suggested branch: {branch_name}")
    print("  ⚠️  Branch not created yet - please confirm involved projects first")

    # 3. Create requirement documents
    print("\n📝 Creating requirement documents...")
    doc_manager = get_requirement_doc_manager()

    try:
        docs = doc_manager.create_all_documents(story, branch_name, date, story.get("version", ""), force=force)
        results["docs_dir"] = docs["requirement"].parent
        results["docs"] = docs

        print(f"✓ Documents created in: {docs['requirement'].parent}")
        for doc_type, doc_path in docs.items():
            print(f"  - {doc_path.name}")
    except Exception as e:
        print(f"✗ Failed to create documents: {e}")
        raise

    # 4. Update TAPD status to 'developing'
    print("\n🔄 Updating TAPD status...")
    config = get_config_manager().get_tapd_config()
    target_status = config["tapd"]["workflow"]["start_dev"]

    try:
        tapd_client.update_story_status(
            story_id=story_id,
            status=target_status,
            comment=f"开始需求分析，建议分支: {branch_name}",
        )
        results["status_updated"] = True
        print(f"✓ Status updated to: {target_status}")
    except Exception as e:
        print(f"⚠ Warning: Failed to update status: {e}")
        # Don't raise - status update is not critical

    print("\n" + "=" * 80)
    print("✅ Development preparation completed!")
    print(f"\n📂 Requirement docs: {results['docs_dir']}")
    print(f"🌿 Suggested branch: {results['branch_name']}")
    print(f"🔗 TAPD: https://www.tapd.cn/35238004/prong/stories/view/{story_id}")
    print("\n💡 Next steps:")
    print("  1. Review requirement.md - understand the requirement")
    print("  2. Fill in development.md - specify involved projects")
    print("  3. Update implementationPlan.md - plan your implementation")
    print("  4. Create branch: git checkout -b <branch-name>")
    print("  5. Start coding")

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start development workflow for TAPD story",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start development for a story
  python start_dev.py --story-id 1135238004001009034

  # Start development with specific date
  python start_dev.py --story-id 1135238004001009034 --date 20260304
        """,
    )
    parser.add_argument(
        "--story-id",
        required=True,
        help="TAPD story ID",
    )
    parser.add_argument(
        "--date",
        help="Date string (YYYYMMDD). Defaults to today.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting",
    )

    args = parser.parse_args()

    try:
        start_development(args.story_id, args.date, args.force)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
