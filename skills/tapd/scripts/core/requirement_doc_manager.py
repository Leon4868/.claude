#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Requirement document management for TAPD workflow automation."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config_manager import get_config_manager


class RequirementDocManager:
    """Manages requirement documentation."""

    def __init__(self):
        """Initialize requirement document manager."""
        self.config = get_config_manager().get_requirement_doc_config()
        self.root_dir = Path(self.config["requirement_doc"]["root_dir"])
        self.templates_dir = Path(__file__).parent.parent.parent / "templates"

    def _shorten_name(self, name: str, max_length: int = None) -> str:
        """Shorten story name for directory naming.

        Args:
            name: Story name
            max_length: Maximum length. Defaults to config value.

        Returns:
            Shortened name
        """
        if max_length is None:
            max_length = self.config["requirement_doc"]["max_name_length"]

        # Remove prefix like 【管理后台】
        name_clean = re.sub(r"【[^】]+】", "", name).strip()

        # Truncate if too long
        if len(name_clean) > max_length:
            name_clean = name_clean[:max_length]

        return name_clean

    def _extract_date_from_version(self, version: str) -> str:
        """Extract date from TAPD version string.

        Args:
            version: TAPD version string (e.g., "2026-03-15", "2026.03.15", "20260315")

        Returns:
            Date string in YYYYMMDD format

        Example:
            >>> manager = RequirementDocManager()
            >>> date = manager._extract_date_from_version("2026-03-15")
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

    def format_dir_name(self, story_id: str, story_name: str, date: str = None, version: str = None) -> str:
        """Format requirement directory name.

        Args:
            story_id: Story ID
            story_name: Story name
            date: Date string (YYYYMMDD). If None and version is provided, extracts from version.
                  If both None, defaults to today.
            version: TAPD version string (e.g., "2026-03-15"). Used to extract date if date is None.

        Returns:
            Formatted directory name

        Example:
            >>> manager = RequirementDocManager()
            >>> name = manager.format_dir_name('1135238004001009034', '智能任务详情查询', version='2026-03-15')
            >>> print(name)
            '1135238004001009034_智能任务详情查询_20260315'
        """
        if date is None:
            if version:
                # Extract date from version string (format: YYYY-MM-DD or similar)
                date = self._extract_date_from_version(version)
            else:
                date = datetime.now().strftime("%Y%m%d")

        story_name_short = self._shorten_name(story_name)
        dir_format = self.config["requirement_doc"]["dir_format"]

        return dir_format.format(
            story_id=story_id,
            story_name_short=story_name_short,
            date=date,
        )

    def create_requirement_dir(self, story_id: str, story_name: str, date: str = None, version: str = None) -> Path:
        """Create requirement directory.

        Args:
            story_id: Story ID
            story_name: Story name
            date: Date string (YYYYMMDD). If None and version is provided, extracts from version.
            version: TAPD version string. Used to extract date if date is None.

        Returns:
            Path to created directory

        Example:
            >>> manager = RequirementDocManager()
            >>> dir_path = manager.create_requirement_dir('1135238004001009034', '智能任务详情查询', version='2026-03-15')
        """
        dir_name = self.format_dir_name(story_id, story_name, date, version)
        dir_path = self.root_dir / dir_name

        # Create directory if not exists
        dir_path.mkdir(parents=True, exist_ok=True)

        return dir_path

    def get_requirement_dir(self, story_id: str) -> Optional[Path]:
        """Get requirement directory path by story ID.

        Args:
            story_id: Story ID

        Returns:
            Path to requirement directory or None if not found

        Example:
            >>> manager = RequirementDocManager()
            >>> dir_path = manager.get_requirement_dir('1135238004001009034')
        """
        if not self.root_dir.exists():
            return None

        # Find directory starting with story_id
        for dir_path in self.root_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith(story_id):
                return dir_path

        return None

    def _load_template(self, template_name: str) -> str:
        """Load template content.

        Args:
            template_name: Template file name

        Returns:
            Template content
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            return f"# {template_name}\n\n[Template not found]"

        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_requirement_doc(self, story: Dict[str, Any], output_dir: Path) -> Path:
        """Generate requirement document from story data.

        Args:
            story: Story data dictionary
            output_dir: Output directory

        Returns:
            Path to generated document

        Example:
            >>> manager = RequirementDocManager()
            >>> story = {'id': '123', 'name': 'Test', 'owner': 'User'}
            >>> doc_path = manager.generate_requirement_doc(story, Path('/tmp/req'))
        """
        template = self._load_template("requirement_template.md")

        # Format template with story data
        content = template.format(
            story_id=story.get("id", ""),
            story_name=story.get("name", ""),
            owner=story.get("owner", ""),
            priority=story.get("priority", ""),
            status=story.get("status", ""),
            version=story.get("version", ""),
            created=story.get("created", ""),
            description=story.get("description", "[待补充]"),
            acceptance_criteria=story.get("acceptance_criteria", "[待补充]"),
            attachments=story.get("attachments", "[无]"),
        )

        # Write to file
        doc_path = output_dir / self.config["requirement_doc"]["templates"]["requirement"]
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        return doc_path

    def create_implementation_plan_template(self, output_dir: Path) -> Path:
        """Create implementation plan template.

        Args:
            output_dir: Output directory

        Returns:
            Path to created template
        """
        template = self._load_template("implementation_plan_template.md")
        doc_path = output_dir / self.config["requirement_doc"]["templates"]["implementation_plan"]

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(template)

        return doc_path

    def create_development_doc(self, output_dir: Path, story: Dict[str, Any], branch_name: str) -> Path:
        """Create development document with branch and project info.

        Args:
            output_dir: Output directory
            story: Story data to pre-fill template
            branch_name: Suggested branch name

        Returns:
            Path to created document
        """
        template = self._load_template("development_template.md")

        # Pre-fill with story data
        content = template.format(
            story_id=story.get("id", ""),
            story_name=story.get("name", ""),
            start_date=datetime.now().strftime("%Y-%m-%d"),
            owner=story.get("owner", ""),
            branch_name=branch_name,
        )

        doc_path = output_dir / self.config["requirement_doc"]["templates"]["development"]

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        return doc_path

    def create_release_template(self, output_dir: Path, story: Dict[str, Any] = None) -> Path:
        """Create release document template.

        Args:
            output_dir: Output directory
            story: Optional story data to pre-fill template

        Returns:
            Path to created template
        """
        template = self._load_template("release_template.md")

        if story:
            # Pre-fill with story data
            content = template.format(
                story_id=story.get("id", ""),
                story_name=story.get("name", ""),
                version=story.get("version", ""),
                release_date="",
                owner=story.get("owner", ""),
            )
        else:
            content = template

        doc_path = output_dir / self.config["requirement_doc"]["templates"]["release"]

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        return doc_path

    def create_claude_doc(self, output_dir: Path, story: Dict[str, Any], branch_name: str) -> Path:
        """Create Claude Code context document.

        Args:
            output_dir: Output directory
            story: Story data to pre-fill template
            branch_name: Suggested branch name

        Returns:
            Path to created document
        """
        template = self._load_template("claude_template.md")

        # Get code_root_dir from git config
        git_config = get_config_manager().get_git_config()
        code_root_dir = git_config.get("git", {}).get("code_root_dir", "")
        # If env var not set, it stays as "${CODE_ROOT_DIR}" string
        if not code_root_dir or code_root_dir.startswith("${"):
            code_root_dir = ""

        # Pre-fill with story data
        projects = "[待填写]"

        content = template.format(
            story_id=story.get("id", ""),
            story_name=story.get("name", ""),
            priority=story.get("priority", ""),
            version=story.get("version", ""),
            description=story.get("description", "[待补充]"),
            projects=projects,
            code_root_dir=code_root_dir if code_root_dir else "[待填写]",
            branch_name=branch_name,
            base_branch="[待确认]",  # Will be filled when creating branch
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )

        doc_path = output_dir / self.config["requirement_doc"]["templates"]["claude"]

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)

        return doc_path

    def create_all_documents(self, story: Dict[str, Any], branch_name: str = None, date: str = None, version: str = None, force: bool = False) -> Dict[str, Path]:
        """Create all requirement documents for a story.

        Args:
            story: Story data dictionary
            branch_name: Optional branch name for development doc
            date: Date string (YYYYMMDD). If None and version is provided, extracts from version.
            version: TAPD version string. Used to extract date if date is None.
            force: If True, overwrite existing files without prompting

        Returns:
            Dictionary mapping document type to file path

        Raises:
            FileExistsError: If directory exists and user chooses not to overwrite

        Example:
            >>> manager = RequirementDocManager()
            >>> story = {'id': '123', 'name': 'Test Story', 'version': '2026-03-15'}
            >>> docs = manager.create_all_documents(story)
            >>> print(docs['requirement'])
        """
        # Use version from story if not provided
        if version is None and 'version' in story:
            version = story['version']

        # Create requirement directory
        req_dir = self.create_requirement_dir(
            story.get("id", ""),
            story.get("name", ""),
            date,
            version,
        )

        # Check if any documents already exist
        if not force:
            existing_files = []
            doc_names = {
                "requirement": self.config["requirement_doc"]["templates"]["requirement"],
                "development": self.config["requirement_doc"]["templates"]["development"],
                "implementation_plan": self.config["requirement_doc"]["templates"]["implementation_plan"],
                "release": self.config["requirement_doc"]["templates"]["release"],
                "claude": self.config["requirement_doc"]["templates"]["claude"],
            }

            for doc_type, doc_name in doc_names.items():
                doc_path = req_dir / doc_name
                if doc_path.exists():
                    existing_files.append(doc_name)

            if existing_files:
                error_msg = f"需求文档目录已存在，以下文件将被覆盖：\n"
                for file_name in existing_files:
                    error_msg += f"  - {file_name}\n"
                error_msg += f"\n目录位置：{req_dir}\n"
                error_msg += f"\n如需覆盖，请使用 --force 参数"
                raise FileExistsError(error_msg)

        # Generate branch name if not provided
        if branch_name is None:
            from .git_helper import get_git_helper
            git_helper = get_git_helper()
            branch_name = git_helper.format_branch_name(
                story_id=story.get("id", ""),
                story_name=story.get("name", ""),
                date=date,
                version=version,
            )

        # Create all documents (removed todo)
        docs = {
            "requirement": self.generate_requirement_doc(story, req_dir),
            "development": self.create_development_doc(req_dir, story, branch_name),
            "implementation_plan": self.create_implementation_plan_template(req_dir),
            "release": self.create_release_template(req_dir, story),
            "claude": self.create_claude_doc(req_dir, story, branch_name),
        }

        return docs


def get_requirement_doc_manager() -> RequirementDocManager:
    """Get RequirementDocManager instance."""
    return RequirementDocManager()
