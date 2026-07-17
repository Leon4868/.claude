#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query TAPD stories."""

import argparse
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
import yaml

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from tapd_client import TAPDClient


def load_user_config():
    """Load user configuration."""
    config_path = Path(__file__).parent.parent / "config" / "user_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_default_owner():
    """Get default owner from user config."""
    try:
        config = load_user_config()
        if config.get("initialized", False):
            return config["user"]["tapd_username"]
    except Exception:
        pass
    return None


def get_default_version():
    """Get default version based on current date.

    Rules:
    - If today is before Friday (Mon-Thu): use this Thursday's date
    - If today is Friday or after (Fri-Sun): use next Thursday's date

    Returns:
        Version string in format "YYYY-MMDD" (e.g., "2026-0312")
    """
    today = datetime.now()
    weekday = today.weekday()  # Monday=0, Sunday=6

    # Thursday is weekday 3
    if weekday < 4:  # Monday to Thursday (0-3)
        # Use this week's Thursday
        days_to_thursday = 3 - weekday
        target_date = today + timedelta(days=days_to_thursday)
    else:  # Friday to Sunday (4-6)
        # Use next week's Thursday
        days_to_next_thursday = (3 - weekday) + 7
        target_date = today + timedelta(days=days_to_next_thursday)

    # Format as "YYYY-MMDD"
    return target_date.strftime("%Y-%m%d")


def format_story(story, status_map):
    """Format story as a summary line."""
    story_id = story.get('id', '')
    # Extract short ID (last 7 digits)
    short_id = story_id[-7:] if len(story_id) > 7 else story_id
    name = story.get('name', '')
    status = story.get('status', '')
    status_name = status_map.get(status, status)
    priority = story.get('priority', '')
    return f"[{short_id}] {name} (状态: {status_name}, 优先级: {priority})"
    status_name = status_map.get(status, status)
    priority = story.get('priority', '')
    return f"[{story_id}] {name} (状态: {status_name}, 优先级: {priority})"


def query_my_stories(owner, version=None):
    """Query stories owned by specific user.

    Args:
        owner: Story owner name
        version: Story version (optional, will use default if not provided)
    """
    client = TAPDClient()

    # Use default version if not provided
    if not version:
        version = get_default_version()

    stories = client.query_stories(owner=owner, version=version)

    # Group by status
    status_groups = {}
    for story in stories:
        status = story.get('status', 'unknown')
        status_name = client.status_map.get(status, status)
        if status_name not in status_groups:
            status_groups[status_name] = []
        status_groups[status_name].append(story)

    # Print summary
    print(f"\n查询条件: 处理人={owner}, 版本={version}")
    print(f"你的需求（共 {len(stories)} 个）：\n")
    for status_name, items in sorted(status_groups.items()):
        print(f"{status_name}（{len(items)}个）：")
        for story in items:
            print(f"  {format_story(story, client.status_map)}")
        print()


def query_story_detail(story_id):
    """Query story detail by ID.

    Args:
        story_id: Story ID (can be short ID like "1009034" or full ID)
    """
    client = TAPDClient()
    story = client.get_story_detail(story_id)

    full_id = story.get('id', '')
    short_id = full_id[-7:] if len(full_id) > 7 else full_id

    print(f"\n需求详情：\n")
    print(f"Short ID: {short_id}")
    print(f"Full ID: {full_id}")
    print(f"名称: {story.get('name')}")
    print(f"状态: {story.get('status')}")
    print(f"负责人: {story.get('owner')}")
    print(f"优先级: {story.get('priority')}")
    print(f"版本: {story.get('version', '未设置')}")
    print(f"创建时间: {story.get('created')}")
    print(f"修改时间: {story.get('modified')}")
    if story.get('description'):
        print(f"\n描述:\n{story.get('description')[:500]}...")


def query_by_filters(owner=None, version=None):
    """Query stories by owner and/or version."""
    client = TAPDClient()
    stories = client.query_stories(owner=owner, version=version)

    filters = []
    if owner:
        filters.append(f"处理人: {owner}")
    if version:
        filters.append(f"版本: {version}")

    print(f"\n查询条件: {', '.join(filters)}")
    print(f"找到 {len(stories)} 个需求：\n")

    for story in stories:
        print(f"  {format_story(story, client.status_map)}")
        print(f"    版本: {story.get('version', '未设置')}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Query TAPD stories')
    parser.add_argument('mode', choices=['my', 'detail', 'query'],
                        help='Query mode')
    parser.add_argument('--owner', help='Story owner')
    parser.add_argument('--version', help='Story version')
    parser.add_argument('--story-id', help='Story ID for detail mode')

    args = parser.parse_args()

    try:
        if args.mode == 'my':
            owner = args.owner or get_default_owner()
            if not owner:
                print("Error: --owner is required or run 'init_config.py' first")
                sys.exit(1)
            query_my_stories(owner, version=args.version)
        elif args.mode == 'detail':
            if not args.story_id:
                print("Error: --story-id is required for detail mode")
                sys.exit(1)
            query_story_detail(args.story_id)
        elif args.mode == 'query':
            if not args.owner and not args.version:
                print("Error: --owner or --version is required for query mode")
                sys.exit(1)
            query_by_filters(owner=args.owner, version=args.version)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
