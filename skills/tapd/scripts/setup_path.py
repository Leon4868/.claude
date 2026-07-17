#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup script for TAPD requirements directory configuration (non-interactive)."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.path_setup import get_requirements_dir


def main():
    """Run setup (non-interactive)."""
    print("=" * 60)
    print("TAPD 需求文档目录配置")
    print("=" * 60)

    try:
        path = get_requirements_dir()
        print("\n" + "=" * 60)
        print("✓ 配置成功!")
        print(f"需求文档目录: {path}")
        print("=" * 60)
        print("\n提示:")
        print("- 如需自定义路径，请设置环境变量 TAPD_REQUIREMENTS_DIR")
        print("- 默认路径: ~/tapd-requirements")
        return 0
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
