#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create TAPD story."""

import argparse
import json
import sys
import io
import base64
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import get_config_manager
import os


def create_story(name, description, owner="连武坤", priority="3", version=""):
    """Create a new TAPD story.

    Args:
        name: Story name
        description: Story description
        owner: Story owner (default: 连武坤)
        priority: Priority 1-4 (default: 3)
        version: Target version/iteration

    Returns:
        Created story data
    """
    config = get_config_manager().get_tapd_config()

    token = os.getenv(config["tapd"]["token_env"])
    if not token:
        raise ValueError(f"TAPD token not found. Set {config['tapd']['token_env']} environment variable.")

    workspace_id = config["tapd"]["workspace_id"]
    base_url = config["tapd"]["base_url"].rstrip("/")

    # Prepare form data
    data = {
        "workspace_id": workspace_id,
        "name": name,
        "owner": owner,
        "priority": priority,
    }

    # Add description if provided
    if description:
        data["description"] = description

    # Add iteration if provided
    if version:
        data["iteration_id"] = version

    # Encode form data
    encoded_data = urlencode(data).encode('utf-8')
    url = f"{base_url}/stories"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": str(len(encoded_data))
    }

    request = Request(url, data=encoded_data, headers=headers, method="POST")

    try:
        print(f"创建需求: {name}")
        print(f"工作空间: {workspace_id}")
        print(f"负责人: {owner}")

        with urlopen(request, timeout=30) as response:
            payload = json.load(response)

        if payload.get("status") != 1:
            raise RuntimeError(f"TAPD API error: {payload.get('info')}")

        story_data = payload.get("data", {})
        if isinstance(story_data, dict) and "Story" in story_data:
            return story_data["Story"]
        return story_data

    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"Response: {error_body}")
        except:
            pass
        raise
    except Exception as e:
        print(f"Error creating story: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    parser = argparse.ArgumentParser(description='Create TAPD story')
    parser.add_argument('--name', required=True, help='Story name')
    parser.add_argument('--description', default='', help='Story description')
    parser.add_argument('--owner', default='连武坤', help='Story owner')
    parser.add_argument('--priority', default='3', choices=['1', '2', '3', '4'], help='Priority (1-4)')
    parser.add_argument('--iteration', default='', help='Target iteration/version')

    args = parser.parse_args()

    try:
        story = create_story(
            name=args.name,
            description=args.description,
            owner=args.owner,
            priority=args.priority,
            version=args.iteration
        )

        print(f"\n需求创建成功！\n")
        print(f"ID: {story.get('id')}")
        print(f"名称: {story.get('name')}")
        print(f"负责人: {story.get('owner')}")
        print(f"优先级: {story.get('priority')}")
        if story.get('iteration_id'):
            print(f"迭代: {story.get('iteration_id')}")
        print(f"\n查看详情: https://www.tapd.cn/35238004/prong/stories/view/{story.get('id')}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
