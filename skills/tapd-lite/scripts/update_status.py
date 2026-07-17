#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update TAPD story status."""

import argparse
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from tapd_client import TAPDClient


def update_story_status(story_id, status):
    """Update story status.

    Args:
        story_id: Short ID (7 digits) or full ID (19 digits)
        status: New status

    Returns:
        Updated story data
    """
    client = TAPDClient()

    # Get current status
    story = client.get_story_detail(story_id)
    full_id = story.get('id', '')
    short_id = TAPDClient.get_short_id(full_id)
    old_status = story.get('status', '')
    old_status_name = client.status_map.get(old_status, old_status)

    # Update status
    updated_story = client.update_story_status(story_id, status)
    new_status_name = client.status_map.get(status, status)

    # Output results with short_id
    print(f"SHORT_ID={short_id}")
    print(f"FULL_ID={full_id}")
    print(f"STORY_NAME={story.get('name', '')}")
    print(f"OLD_STATUS={old_status}")
    print(f"OLD_STATUS_NAME={old_status_name}")
    print(f"NEW_STATUS={status}")
    print(f"NEW_STATUS_NAME={new_status_name}")
    print(f"SUCCESS=true")

    return updated_story


def main():
    parser = argparse.ArgumentParser(description='Update TAPD story status')
    parser.add_argument('story_id', help='Story ID')
    parser.add_argument('status', help='New status')

    args = parser.parse_args()

    try:
        update_story_status(args.story_id, args.status)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
