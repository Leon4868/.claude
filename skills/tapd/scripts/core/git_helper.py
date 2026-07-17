#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Git operations helper for TAPD workflow automation."""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config_manager import get_config_manager


class GitHelper:
    """Helper class for Git operations."""

    def __init__(self, repo_path: str = None):
        """Initialize Git helper.

        Args:
            repo_path: Path to git repository. Defaults to current directory.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.config = get_config_manager().get_git_config()

        # Auto-detect username if not configured
        if not self.config["git"]["username"] or self.config["git"]["username"].startswith("${"):
            try:
                self.config["git"]["username"] = self.get_git_username()
            except:
                self.config["git"]["username"] = "unknown"

        # Auto-detect username abbreviation if not configured
        if not self.config["git"]["username_abbr"] or self.config["git"]["username_abbr"].startswith("${"):
            # Try to generate abbreviation from username
            username = self.config["git"]["username"]
            # For Chinese names, use pinyin initials; for English, use lowercase
            if any('\u4e00' <= c <= '\u9fff' for c in username):
                # Chinese name - user should set GIT_USERNAME_ABBR manually
                self.config["git"]["username_abbr"] = username[:3] if len(username) <= 3 else username[:2]
            else:
                # English name - use lowercase
                self.config["git"]["username_abbr"] = username.lower().replace(" ", "")

    def _extract_date_from_version(self, version: str) -> str:
        """Extract date from TAPD version string.

        Args:
            version: TAPD version string (e.g., "2026-03-15", "2026.03.15", "20260315")

        Returns:
            Date string in YYYYMMDD format

        Example:
            >>> git = GitHelper()
            >>> date = git._extract_date_from_version("2026-03-15")
            >>> print(date)
            '20260315'
        """
        # Remove common separators and extract digits
        version_clean = re.sub(r"[^\d]", "", version)

        # If already in YYYYMMDD format (8 digits)
        if len(version_clean) >= 8:
            return version_clean[:8]

        # Fallback to current date if parsing fails
        return datetime.now().strftime("%Y%m%d")

    def _run_command(self, cmd: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run git command.

        Args:
            cmd: Command and arguments
            check: Whether to raise exception on error

        Returns:
            CompletedProcess instance
        """
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
            encoding="utf-8",
        )

    def _get_base_branch_config(self):
        """Get base branch config in both legacy and new formats."""
        base_branch_config = self.config["git"].get("base_branch", "develop")
        if isinstance(base_branch_config, dict):
            return base_branch_config
        return {
            "pattern": None,
            "fallback": base_branch_config,
            "sort_by": "both",
        }

    def _get_all_branches(self):
        """Get all local and remote branch names without duplicates."""
        result = self._run_command(["git", "branch", "-a"])
        branches = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or '->' in line:
                continue
            branch = line.lstrip('* ').strip()
            if branch.startswith('remotes/origin/'):
                branch = branch.replace('remotes/origin/', '')
            branches.append(branch)
        return list(set(branches))

    def _get_branch_commit_time(self, branch: str) -> int:
        """Get last commit timestamp for branch."""
        try:
            result = self._run_command(["git", "log", "-1", "--format=%ct", branch])
            return int(result.stdout.strip()) if result.stdout.strip() else 0
        except Exception:
            return 0

    def find_base_branch(self) -> str:
        """Find latest base branch, preferring latest release branch."""
        base_config = self._get_base_branch_config()
        pattern = base_config.get("pattern")
        fallback = base_config.get("fallback", "develop")
        sort_by = base_config.get("sort_by", "both")

        self._run_command(["git", "fetch", "--all"], check=False)
        branches = self._get_all_branches()
        if not branches:
            return fallback

        if pattern:
            regex = re.compile(pattern)
            branches = [b for b in branches if regex.match(b)]

        if not branches:
            return fallback

        if sort_by == "commit_time":
            branches.sort(key=lambda b: self._get_branch_commit_time(b), reverse=True)
        else:
            branches.sort(reverse=True)

        return branches[0]

    def get_current_branch(self) -> str:
        """Get current branch name.

        Returns:
            Current branch name

        Example:
            >>> git = GitHelper()
            >>> branch = git.get_current_branch()
            >>> print(branch)
            'lwk/feature_智能任务详情查询_1135238004001009034_20260304'
        """
        result = self._run_command(["git", "branch", "--show-current"])
        return result.stdout.strip()

    def create_branch(self, branch_name: str, base_branch: str = None) -> bool:
        """Create and checkout new branch.

        Args:
            branch_name: Name of new branch
            base_branch: Base branch to create from. Defaults to latest release branch.

        Returns:
            True if successful
        """
        if base_branch is None:
            base_branch = self.find_base_branch()

        self._run_command(["git", "fetch", "--all"], check=False)

        # Ensure we're on base branch from latest release
        checkout_result = self._run_command(["git", "checkout", base_branch], check=False)
        if checkout_result.returncode != 0:
            self._run_command(["git", "checkout", "-B", base_branch, f"origin/{base_branch}"])

        # Pull latest changes
        self._run_command(["git", "pull"], check=False)

        # Create and checkout new branch from current HEAD
        self._run_command(["git", "checkout", "-b", branch_name])

        # Safety: feature branch must not track base/release branch
        self._run_command(["git", "branch", "--unset-upstream", branch_name], check=False)

        return True

    def format_branch_name(
        self,
        story_id: str,
        story_name: str,
        date: str = None,
        version: str = None,
        username_abbr: str = None,
    ) -> str:
        """Format branch name according to naming convention.

        Args:
            story_id: TAPD story ID
            story_name: Story name
            date: Date string (YYYYMMDD). If None and version is provided, extracts from version.
                  If both None, defaults to today.
            version: TAPD version string (e.g., "2026-03-15"). Used to extract date if date is None.
            username_abbr: Username abbreviation. Defaults to config value.

        Returns:
            Formatted branch name
        """
        if date is None:
            if version:
                date = self._extract_date_from_version(version)
            else:
                date = datetime.now().strftime("%Y%m%d")
        if username_abbr is None:
            username_abbr = self.config["git"]["username_abbr"]

        story_name_clean = re.sub(r"【[^】]+】", "", story_name).strip()
        story_name_clean = re.sub(r"[^\w\u4e00-\u9fff]+", "_", story_name_clean)

        branch_format = self.config["git"]["branch_format"]
        return branch_format.format(
            username_abbr=username_abbr,
            story_name=story_name_clean,
            story_id=story_id,
            date=date,
        )

    def extract_story_id_from_branch(self, branch_name: str = None) -> Optional[str]:
        """Extract TAPD story ID from branch name."""
        if branch_name is None:
            branch_name = self.get_current_branch()

        pattern = r"_(\d{19})_\d{8}$"
        match = re.search(pattern, branch_name)
        if match:
            return match.group(1)

        pattern = r"(\d{19})"
        match = re.search(pattern, branch_name)
        if match:
            return match.group(1)

        return None

    def commit(self, message: str, story_id: str = None) -> bool:
        """Commit changes with formatted message."""
        if story_id is None:
            story_id = self.extract_story_id_from_branch()

        if story_id:
            commit_format = self.config["git"]["commit_format"]
            formatted_message = commit_format.format(story_id=story_id, message=message)
        else:
            formatted_message = message

        self._run_command(["git", "commit", "-m", formatted_message])
        return True

    def push(self, branch: str = None, set_upstream: bool = True) -> bool:
        """Push branch to remote."""
        if branch is None:
            branch = self.get_current_branch()

        cmd = ["git", "push"]
        if set_upstream:
            cmd.extend(["-u", "origin", branch])
        else:
            cmd.append("origin")
            cmd.append(branch)

        self._run_command(cmd)
        return True

    def get_git_username(self) -> str:
        result = self._run_command(["git", "config", "user.name"])
        return result.stdout.strip()

    def get_git_email(self) -> str:
        result = self._run_command(["git", "config", "user.email"])
        return result.stdout.strip()

    def has_uncommitted_changes(self) -> bool:
        result = self._run_command(["git", "status", "--porcelain"])
        return bool(result.stdout.strip())


def get_git_helper() -> GitHelper:
    """Get GitHelper instance."""
    return GitHelper()
