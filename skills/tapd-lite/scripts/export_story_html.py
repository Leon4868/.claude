#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export story description to HTML file."""

import argparse
import sys
import io
import re
from pathlib import Path

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from tapd_client import TAPDClient


def export_story_to_html(story_id, output_dir=None):
    """Export story description to HTML file.

    Args:
        story_id: Story ID (can be short ID or full ID)
        output_dir: Output directory (default: current directory)
    """
    client = TAPDClient()
    story = client.get_story_detail(story_id)

    full_id = story.get('id', '')
    short_id = full_id[-7:] if len(full_id) > 7 else full_id
    name = story.get('name', 'untitled')
    description = story.get('description', '')

    # Create HTML file content with basic styling
    content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 15px 0;
            color: #333;
        }}
        .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        .meta-item {{
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }}
        .meta-label {{
            font-weight: bold;
            color: #666;
        }}
        .content {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        table th, table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        table th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 15px 0;
            padding-left: 15px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{name}</h1>
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">需求ID:</span> {short_id} (完整ID: {full_id})
            </div>
            <div class="meta-item">
                <span class="meta-label">状态:</span> {story.get('status', '未知')}
            </div>
            <div class="meta-item">
                <span class="meta-label">负责人:</span> {story.get('owner', '未指定')}
            </div>
            <div class="meta-item">
                <span class="meta-label">优先级:</span> {story.get('priority', '未设置')}
            </div>
            <div class="meta-item">
                <span class="meta-label">版本:</span> {story.get('version', '未设置')}
            </div>
            <div class="meta-item">
                <span class="meta-label">创建时间:</span> {story.get('created', '未知')}
            </div>
            <div class="meta-item">
                <span class="meta-label">修改时间:</span> {story.get('modified', '未知')}
            </div>
        </div>
    </div>

    <div class="content">
        <h2>需求描述</h2>
        {description}
    </div>
</body>
</html>
"""

    # Sanitize filename (remove invalid characters)
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
    filename = f"{safe_name}.html"

    # Determine output path
    if output_dir:
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(filename)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Output result in key-value format
    print(f"SUCCESS=true")
    print(f"STORY_ID={full_id}")
    print(f"SHORT_ID={short_id}")
    print(f"STORY_NAME={name}")
    print(f"OUTPUT_FILE={output_path.absolute()}")
    print(f"FILE_SIZE={output_path.stat().st_size}")


def main():
    parser = argparse.ArgumentParser(description='Export story description to HTML')
    parser.add_argument('story_id', help='Story ID (short ID or full ID)')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: current directory)')

    args = parser.parse_args()

    try:
        export_story_to_html(args.story_id, args.output_dir)
    except Exception as e:
        print(f"ERROR={e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
