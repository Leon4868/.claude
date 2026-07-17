#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate branch name from story ID."""

import argparse
import sys
import io
import os
import re
from datetime import datetime
from pathlib import Path
import yaml

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from tapd_client import TAPDClient


def simplify_story_name(name, max_length=21):
    """Simplify story name if it exceeds max_length.

    Args:
        name: Original story name
        max_length: Maximum length (default 21)

    Returns:
        Simplified story name

    Examples:
        "智能任务详情查询" -> "智能任务详情查询" (8 chars, keep as is)
        "智能任务策略模板条件支持有效接通次数统计" -> "智能任务策略模板条件有效接通次数" (extract core)
        "新版智能任务要覆盖的企业特殊配置" -> "新版智能任务企业特殊配置" (extract core)
    """
    if len(name) <= max_length:
        return name

    # Remove common verbs and auxiliary words
    remove_words = ['支持', '实现', '优化', '新增', '修复', '调整', '完善', '增加',
                    '要', '的', '和', '与', '或', '等', '及', '对', '为', '在']

    # Try to extract core nouns
    simplified = name
    for word in remove_words:
        simplified = simplified.replace(word, '')

    # If still too long, truncate
    if len(simplified) > max_length:
        simplified = simplified[:max_length]

    return simplified


def get_short_id(story_id):
    """Extract short ID from full story ID.

    Args:
        story_id: Full story ID (e.g., "1135238004001009034")

    Returns:
        Short ID (e.g., "1009034")

    Examples:
        "1135238004001009034" -> "1009034" (last 7 digits)
        "1135238004001008977" -> "1008977"
    """
    # TAPD story ID format: {workspace_id}{story_number}
    # workspace_id is typically 8-11 digits, story_number is the rest
    # We take the last 7 digits as short_id
    if len(story_id) > 7:
        return story_id[-7:]
    return story_id


def generate_branch_name(story_id, custom_name=None):
    """Generate branch name from story ID.

    Args:
        story_id: Story ID
        custom_name: Custom story name (optional, for user confirmation)
    """
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "git_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Get username abbreviation
    username_abbr = os.getenv("GIT_USERNAME_ABBR", config["git"]["username_abbr"])
    if username_abbr.startswith("${") and username_abbr.endswith("}"):
        # Extract default value from ${VAR:default}
        if ":" in username_abbr:
            username_abbr = username_abbr.split(":")[1].rstrip("}")
        else:
            username_abbr = "lwk"

    max_length = config["git"]["max_story_name_length"]

    # Get story details
    client = TAPDClient()
    story = client.get_story_detail(story_id)

    full_id = story.get('id', '')
    short_id = TAPDClient.get_short_id(full_id)
    story_name = story.get('name', '')

    # Use custom name if provided, otherwise simplify automatically
    if custom_name:
        story_name_short = custom_name
    else:
        story_name_short = simplify_story_name(story_name, max_length)

    # Get date from version or use current date
    version = story.get('version', '')

    # Generate branch name (format: username_abbr/feature/short_id_story_name_short)
    branch_name = f"{username_abbr}/feature/{short_id}_{story_name_short}"

    # Output format for Claude to parse
    print(f"FULL_ID={full_id}")
    print(f"SHORT_ID={short_id}")
    print(f"STORY_NAME={story_name}")
    print(f"STORY_NAME_SHORT={story_name_short}")
    print(f"VERSION={version or '未设置'}")
    print(f"BRANCH_NAME={branch_name}")
    print(f"NAME_SIMPLIFIED={'true' if len(story_name) > max_length and not custom_name else 'false'}")

    return branch_name


def main():
    parser = argparse.ArgumentParser(description='Generate branch name from story ID')
    parser.add_argument('story_id', help='Story ID')
    parser.add_argument('--custom-name', help='Custom story name (for user confirmation)')

    args = parser.parse_args()

    try:
        generate_branch_name(args.story_id, args.custom_name)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
