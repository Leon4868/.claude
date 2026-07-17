#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export story description to Markdown file."""

import argparse
import sys
import io
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from tapd_client import TAPDClient

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False


def html_to_markdown_simple(html_content):
    """Simple HTML to Markdown conversion (fallback)."""
    if not html_content:
        return ""

    # Basic replacements
    text = html_content

    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Headers
    for i in range(6, 0, -1):
        text = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', lambda m: '\n' + '#' * i + ' ' + m.group(1) + '\n', text, flags=re.IGNORECASE)

    # Bold and italic
    text = re.sub(r'<(strong|b)>(.*?)</\1>', r'**\2**', text, flags=re.IGNORECASE)
    text = re.sub(r'<(em|i)>(.*?)</\1>', r'*\2*', text, flags=re.IGNORECASE)

    # Links
    text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)

    # Images
    text = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', text, flags=re.IGNORECASE)

    # Line breaks
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<hr\s*/?>', '\n---\n', text, flags=re.IGNORECASE)

    # Paragraphs
    text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)

    # Lists
    text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?[ou]l[^>]*>', '\n', text, flags=re.IGNORECASE)

    # Code
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE)
    text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Blockquote
    text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '\n> ' + m.group(1).replace('\n', '\n> ') + '\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Tables - keep as HTML for now (better than losing content)
    # We'll just add newlines around tables
    text = re.sub(r'<table[^>]*>', '\n<table>', text, flags=re.IGNORECASE)
    text = re.sub(r'</table>', '</table>\n', text, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)

    return text.strip()


def html_to_markdown(html_content):
    """Convert HTML to Markdown using html2text if available."""
    if not html_content:
        return ""

    if HAS_HTML2TEXT:
        h = html2text.HTML2Text()
        h.body_width = 0  # Don't wrap lines
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.skip_internal_links = False
        h.inline_links = True
        h.protect_links = True
        h.unicode_snob = True
        return h.handle(html_content)
    else:
        return html_to_markdown_simple(html_content)


def _load_tapd_cookie():
    """Load TAPD browser cookie from user config."""
    try:
        config_path = Path(__file__).parent.parent / "config" / "user_config.yaml"
        if config_path.exists():
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if config and "user" in config:
                return config["user"].get("tapd_cookie")
    except Exception:
        pass
    return None


def download_images(html_content, images_dir, token):
    """Download images from TAPD and replace URLs with local paths.

    Uses browser cookie for authentication (TAPD web resources require session auth).
    Falls back to full TAPD URLs if cookie is not configured or download fails.

    Args:
        html_content: HTML content with image tags
        images_dir: Directory to save images
        token: TAPD API token (unused, kept for compatibility)

    Returns:
        Tuple of (updated HTML content, number of images downloaded)
    """
    tapd_web_url = "https://file.tapd.cn"
    img_pattern = re.compile(r'(<img[^>]*src=["\'])(/[^"\']+)(["\'][^>]*>)', re.IGNORECASE)
    matches = img_pattern.findall(html_content)

    if not matches:
        return html_content, 0, 0

    cookie = _load_tapd_cookie()
    images_dir = Path(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    failed = 0

    for prefix, url_path, suffix in matches:
        full_url = tapd_web_url + url_path
        filename = url_path.split('/')[-1]
        local_path = images_dir / filename

        success = False

        # Try downloading with cookie first (if available)
        if cookie:
            try:
                headers = {
                    "Cookie": cookie,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.tapd.cn/",
                }
                req = Request(full_url, headers=headers)
                with urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    if len(data) >= 100:
                        with open(local_path, 'wb') as f:
                            f.write(data)
                        success = True
            except (URLError, HTTPError, OSError):
                pass

        # Try downloading without cookie if cookie method failed or not available
        if not success:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
                req = Request(full_url, headers=headers)
                with urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    if len(data) >= 100:
                        with open(local_path, 'wb') as f:
                            f.write(data)
                        success = True
            except (URLError, HTTPError, OSError):
                pass

        if success:
            relative_path = f"images/{filename}"
            html_content = html_content.replace(
                f"{prefix}{url_path}{suffix}",
                f"{prefix}{relative_path}{suffix}"
            )
            downloaded += 1
        else:
            # If download failed, keep the relative path but add a warning comment
            relative_path = f"images/{filename}"
            html_content = html_content.replace(
                f"{prefix}{url_path}{suffix}",
                f"{prefix}{relative_path}{suffix}"
            )
            # Create a placeholder file to indicate download failure
            try:
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(f"Failed to download image from: {full_url}\n")
            except OSError:
                pass
            failed += 1

    # Don't remove images dir even if empty (we might have placeholder files)
    # try:
    #     if images_dir.exists() and not any(images_dir.iterdir()):
    #         images_dir.rmdir()
    # except OSError:
    #     pass

    return html_content, downloaded, failed


def export_story_to_markdown(story_id, output_dir=None):
    """Export story description to Markdown file.

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

    # Sanitize filename (remove invalid characters)
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
    filename = f"{safe_name}.md"

    # Determine output path
    if output_dir:
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(filename)

    # Download images to local directory before markdown conversion
    images_downloaded = 0
    images_failed = 0
    if description:
        images_dir = output_path.parent / "images"
        description, images_downloaded, images_failed = download_images(description, images_dir, client.token)

    # Convert HTML to Markdown
    markdown_content = html_to_markdown(description)

    # Also fix any remaining relative URLs in the markdown output
    # (in case html2text or the converter produced them)
    markdown_content = re.sub(
        r'(!\[[^\]]*\])\((/tfl/[^)]+)\)',
        lambda m: f'{m.group(1)}(https://file.tapd.cn{m.group(2)})',
        markdown_content
    )

    # Create Markdown file content
    content = f"""# {name}

**需求ID**: {short_id} (完整ID: {full_id})
**状态**: {story.get('status', '未知')}
**负责人**: {story.get('owner', '未指定')}
**优先级**: {story.get('priority', '未设置')}
**版本**: {story.get('version', '未设置')}
**创建时间**: {story.get('created', '未知')}
**修改时间**: {story.get('modified', '未知')}

---

## 需求描述

{markdown_content}
"""

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
    print(f"IMAGES_DOWNLOADED={images_downloaded}")
    print(f"IMAGES_FAILED={images_failed}")

    if not HAS_HTML2TEXT:
        print(f"WARNING=html2text not installed, using simple conversion (tables may not render correctly)")


def main():
    parser = argparse.ArgumentParser(description='Export story description to Markdown')
    parser.add_argument('story_id', help='Story ID (short ID or full ID)')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: current directory)')

    args = parser.parse_args()

    try:
        export_story_to_markdown(args.story_id, args.output_dir)
    except Exception as e:
        print(f"ERROR={e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
