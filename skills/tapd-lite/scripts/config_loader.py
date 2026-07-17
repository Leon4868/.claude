#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified configuration loader for all scripts."""

from pathlib import Path
import yaml


class ConfigLoader:
    """Configuration loader singleton."""

    _instance = None
    _configs = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"

    def load_tapd_config(self):
        """Load TAPD configuration."""
        if 'tapd' not in self._configs:
            config_path = self.config_dir / "tapd_config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                self._configs['tapd'] = yaml.safe_load(f)
        return self._configs['tapd']

    def load_git_config(self):
        """Load Git configuration."""
        if 'git' not in self._configs:
            config_path = self.config_dir / "git_config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                self._configs['git'] = yaml.safe_load(f)
        return self._configs['git']

    def load_user_config(self):
        """Load user configuration."""
        if 'user' not in self._configs:
            config_path = self.config_dir / "user_config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                self._configs['user'] = yaml.safe_load(f)
        return self._configs['user']

    def save_user_config(self, config):
        """Save user configuration."""
        config_path = self.config_dir / "user_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        self._configs['user'] = config

    def is_initialized(self):
        """Check if user configuration is initialized."""
        try:
            config = self.load_user_config()
            return config.get("initialized", False)
        except Exception:
            return False

    def get_tapd_username(self):
        """Get TAPD username from user config."""
        try:
            config = self.load_user_config()
            if config.get("initialized", False):
                return config["user"]["tapd_username"]
        except Exception:
            pass
        return None

    def get_git_username_abbr(self):
        """Get Git username abbreviation from user config."""
        try:
            config = self.load_user_config()
            if config.get("initialized", False):
                return config["user"]["git_username_abbr"]
        except Exception:
            pass
        return None

    def get_requirements_dir(self):
        """Get requirements directory from user config."""
        try:
            config = self.load_user_config()
            if config.get("initialized", False):
                req_dir = config["paths"]["requirements_dir"]
                return Path(req_dir).expanduser()
        except Exception:
            pass
        return Path.home() / "tapd-requirements"


# Global instance
config_loader = ConfigLoader()
