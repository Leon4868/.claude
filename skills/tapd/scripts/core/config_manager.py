#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration management for TAPD workflow automation."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

from .path_setup import ensure_requirements_dir


class ConfigManager:
    """Manages configuration loading and access."""

    def __init__(self, config_dir: str = None):
        """Initialize configuration manager.

        Args:
            config_dir: Path to configuration directory. Defaults to project root/config.
        """
        if config_dir is None:
            # Get project root (parent of scripts directory)
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            config_name: Name of config file (without .yaml extension)

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if config_name in self._configs:
            return self._configs[config_name]

        config_path = self.config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Replace environment variables
        config = self._replace_env_vars(config)
        self._configs[config_name] = config
        return config

    def _replace_env_vars(self, obj: Any) -> Any:
        """Recursively replace ${VAR} or ${VAR:default} with environment variables.

        Args:
            obj: Object to process (dict, list, str, or other)

        Returns:
            Processed object with environment variables replaced
        """
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            var_expr = obj[2:-1]
            # Support ${VAR:default} syntax
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                value = os.getenv(var_name)
                if value is None:
                    # Special handling for TAPD_REQUIREMENTS_DIR
                    if var_name == "TAPD_REQUIREMENTS_DIR":
                        # Use non-interactive setup (creates default directory if not configured)
                        requirements_dir = ensure_requirements_dir()
                        return str(requirements_dir)
                    # Expand ~ in default value
                    if default_value.startswith("~"):
                        return str(Path(default_value).expanduser())
                    return default_value
                return value
            else:
                return os.getenv(var_expr, obj)
        return obj

    def get(self, config_name: str, *keys: str, default: Any = None) -> Any:
        """Get configuration value by path.

        Args:
            config_name: Name of config file
            *keys: Path to configuration value (e.g., 'tapd', 'base_url')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = ConfigManager()
            >>> config.get('tapd_config', 'tapd', 'base_url')
            'https://api.tapd.cn'
        """
        config = self.load_config(config_name)
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_tapd_config(self) -> Dict[str, Any]:
        """Get TAPD configuration."""
        return self.load_config("tapd_config")

    def get_git_config(self) -> Dict[str, Any]:
        """Get Git configuration."""
        return self.load_config("git_config")

    def get_requirement_doc_config(self) -> Dict[str, Any]:
        """Get requirement document configuration."""
        return self.load_config("requirement_doc_config")

    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        return self.load_config("workflow_config")


# Global config instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
