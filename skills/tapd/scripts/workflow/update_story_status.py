#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update TAPD story status."""

import argparse
import json
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tapd_api import get_tapd_client
from core.config_manager import get_config_manager


def update_status(story_id, status, comment=None):
    """Update story status.

    Args:
        story_id: Story ID
        status: New status value
        comment: Optional comment
    """
    client = get_tapd_client()
    config = get_config_manager().get_tapd_config()
    status_map = config['tapd']['status_map']

    # Get current story details
    print(f"\n正在查询需求详情...")
    story = client.get_story_detail(story_id)

    current_status = story.get('status', '')
    current_status_name = status_map.get(current_status, current_status)

    print(f"\n需求信息：")
    print(f"  ID: {story.get('id')}")
    print(f"  标题: {story.get('name')}")
    print(f"  当前状态: {current_status_name} ({current_status})")

    # Update status
    print(f"\n正在更新状态为: {status}")
    updated_story = client.update_story_status(story_id, status, comment)

    new_status = updated_story.get('status', '')
    new_status_name = status_map.get(new_status, new_status)

    print(f"\n✓ 状态更新成功！")
    print(f"  新状态: {new_status_name} ({new_status})")
    if comment:
        print(f"  备注: {comment}")


def main():
    parser = argparse.ArgumentParser(description='Update TAPD story status')
    parser.add_argument('--story-id', required=True, help='Story ID')
    parser.add_argument('--status', required=True,
                        help='New status (e.g., developing, resolved, testing, status_4)')
    parser.add_argument('--comment', help='Optional comment')

    args = parser.parse_args()

    try:
        update_status(args.story_id, args.status, args.comment)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

