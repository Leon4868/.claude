#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Path setup for TAPD requirements directory (non-interactive)."""

import os
import sys
from pathlib import Path


def get_requirements_dir() -> Path:
    """Get requirements directory from environment or use default.

    Returns:
        Path to requirements directory
    """
    # Check environment variable first
    env_path = os.getenv('TAPD_REQUIREMENTS_DIR')
    if env_path:
        path = Path(env_path).expanduser().resolve()
        # Create if doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Use default path
    default_path = Path.home() / "tapd-requirements"
    default_path.mkdir(parents=True, exist_ok=True)
    return default_path


def ensure_requirements_dir() -> Path:
    """Ensure requirements directory is configured and exists.

    Returns:
        Path to requirements directory
    """
    return get_requirements_dir()


if __name__ == "__main__":
    # Test the setup
    path = get_requirements_dir()
    print(f"需求文档目录: {path}")


