#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query TAPD stories with various filters."""

import argparse
import json
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tapd_api import get_tapd_client
from core.config_manager import get_config_manager


def format_story_summary(story, status_map):
    """Format story as a summary line."""
    story_id = story.get('id', '')
    name = story.get('name', '')
    status = story.get('status', '')
    status_name = status_map.get(status, status)
    priority = story.get('priority', '')

    return f"[{story_id}] {name} (状态: {status_name}, 优先级: {priority})"


def query_my_stories(owner="连武坤"):
    """Query stories owned by specific user."""
    client = get_tapd_client()
    config = get_config_manager().get_tapd_config()
    status_map = config['tapd']['status_map']

    stories = client.query_stories(owner=owner, limit=100)

    # Group by status
    status_groups = {}
    for story in stories:
        status = story.get('status', 'unknown')
        status_name = status_map.get(status, status)
        if status_name not in status_groups:
            status_groups[status_name] = []
        status_groups[status_name].append(story)

    # Print summary
    print(f"\\n你的需求（共 {len(stories)} 个）：\\n")
    for status_name, items in sorted(status_groups.items()):
        print(f"{status_name}（{len(items)}个）：")
        for story in items:
            print(f"  {format_story_summary(story, status_map)}")
        print()


def query_this_week_stories(owner="连武坤"):
    """Query stories created or modified this week."""
    client = get_tapd_client()
    config = get_config_manager().get_tapd_config()
    status_map = config['tapd']['status_map']

    # Calculate week range
    today = datetime.now()
    weekday = today.weekday()
    week_start = today - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)

    stories = client.query_stories(owner=owner, limit=100)

    # Filter this week's stories
    this_week_stories = []
    for story in stories:
        created = story.get('created', '')
        modified = story.get('modified', '')

        try:
            if created:
                created_date = datetime.strptime(created.split()[0], '%Y-%m-%d')
                if week_start.date() <= created_date.date() <= week_end.date():
                    story['_match_type'] = 'created'
                    story['_match_date'] = created
                    this_week_stories.append(story)
                    continue

            if modified:
                modified_date = datetime.strptime(modified.split()[0], '%Y-%m-%d')
                if week_start.date() <= modified_date.date() <= week_end.date():
                    story['_match_type'] = 'modified'
                    story['_match_date'] = modified
                    this_week_stories.append(story)
        except Exception:
            pass

    # Print summary
    print(f"\n本周范围: {week_start.strftime('%Y-%m-%d')} 到 {week_end.strftime('%Y-%m-%d')}")
    print(f"本周相关需求（共 {len(this_week_stories)} 个）：\n")

    for story in this_week_stories:
        match_type = '创建' if story.get('_match_type') == 'created' else '更新'
        date = story.get('_match_date', '')
        print(f"[{match_type}] {format_story_summary(story, status_map)}")
        print(f"  时间: {date}\n")


def query_story_detail(story_id):
    """Query story detail by ID."""
    client = get_tapd_client()
    story = client.get_story_detail(story_id)

    print(f"\n需求详情：\n")
    print(f"ID: {story.get('id')}")
    print(f"名称: {story.get('name')}")
    print(f"状态: {story.get('status')}")
    print(f"负责人: {story.get('owner')}")
    print(f"优先级: {story.get('priority')}")
    print(f"创建时间: {story.get('created')}")
    print(f"修改时间: {story.get('modified')}")
    print(f"\n描述:\n{story.get('description', '')[:500]}...")


def main():
    parser = argparse.ArgumentParser(description='Query TAPD stories')
    parser.add_argument('--mode', choices=['my', 'week', 'detail'], required=True,
                        help='Query mode: my (my stories), week (this week), detail (story detail)')
    parser.add_argument('--owner', default='连武坤', help='Story owner')
    parser.add_argument('--story-id', help='Story ID for detail mode')

    args = parser.parse_args()

    try:
        if args.mode == 'my':
            query_my_stories(args.owner)
        elif args.mode == 'week':
            query_this_week_stories(args.owner)
        elif args.mode == 'detail':
            if not args.story_id:
                print("Error: --story-id is required for detail mode")
                sys.exit(1)
            query_story_detail(args.story_id)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
