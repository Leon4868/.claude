#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TAPD API client for workflow automation."""

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config_manager import get_config_manager


class TAPDClient:
    """TAPD API client."""

    def __init__(self, token: str = None, workspace_id: str = None, base_url: str = None):
        """Initialize TAPD client.

        Args:
            token: TAPD API token. If None, reads from TAPD_TOKEN env var.
            workspace_id: TAPD workspace ID. If None, reads from config.
            base_url: TAPD API base URL. If None, reads from config.
        """
        config = get_config_manager().get_tapd_config()

        self.token = token or os.getenv(config["tapd"]["token_env"])
        if not self.token:
            raise ValueError(f"TAPD token not found. Set {config['tapd']['token_env']} environment variable.")

        self.workspace_id = workspace_id or config["tapd"]["workspace_id"]
        self.base_url = (base_url or config["tapd"]["base_url"]).rstrip("/")

    def _request(self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET") -> Dict[str, Any]:
        """Make HTTP request to TAPD API.

        Args:
            endpoint: API endpoint (e.g., '/stories')
            params: Query parameters
            method: HTTP method

        Returns:
            API response data

        Raises:
            RuntimeError: If API returns error
        """
        params = params or {}
        params["workspace_id"] = self.workspace_id

        url = f"{self.base_url}{endpoint}"
        if method == "GET" and params:
            url = f"{url}?{urlencode(params)}"

        headers = {"Authorization": f"Bearer {self.token}"}
        request = Request(url, headers=headers, method=method)

        with urlopen(request, timeout=30) as response:
            payload = json.load(response)

        if payload.get("status") != 1:
            raise RuntimeError(f"TAPD API error: {payload.get('info')}")

        return payload.get("data", [])

    def get_story_detail(self, story_id: str) -> Dict[str, Any]:
        """Get story details by ID.

        Args:
            story_id: Story ID

        Returns:
            Story details dictionary

        Example:
            >>> client = TAPDClient()
            >>> story = client.get_story_detail('1135238004001009034')
            >>> print(story['name'])
        """
        data = self._request(f"/stories", params={"id": story_id})
        if not data:
            raise ValueError(f"Story not found: {story_id}")
        return data[0].get("Story", {})

    def query_stories(
        self,
        version: str = None,
        owner: str = None,
        status: str = None,
        name: str = None,
        limit: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Query stories with filters.

        Args:
            version: Version filter
            owner: Owner filter
            status: Status filter
            name: Name filter (partial match)
            limit: Max results per page
            page: Page number

        Returns:
            List of story dictionaries
        """
        params = {"limit": limit, "page": page}
        if version:
            params["version"] = version
        if owner:
            params["owner"] = owner
        if status:
            params["status"] = status
        if name:
            params["name"] = name

        data = self._request("/stories", params=params)
        return [item.get("Story", {}) for item in data]

    def update_story_status(self, story_id: str, status: str, comment: str = None) -> Dict[str, Any]:
        """Update story status.

        Args:
            story_id: Story ID
            status: New status (e.g., 'developing', 'resolved', 'testing')
            comment: Optional comment

        Returns:
            Updated story data
        """
        # Prepare form data
        data = {
            'workspace_id': self.workspace_id,
            'id': story_id,
            'status': status
        }

        if comment:
            data['comment'] = comment

        # Encode form data
        encoded_data = urlencode(data).encode('utf-8')

        # Make POST request
        url = f"{self.base_url}/stories"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        request = Request(url, data=encoded_data, headers=headers, method='POST')

        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)

            if payload.get('status') != 1:
                raise RuntimeError(f"TAPD API error: {payload.get('info')}")

            # Return updated story data
            data = payload.get('data', {})
            if data:
                return data.get('Story', {})
            return {}
        except Exception as e:
            raise RuntimeError(f"Failed to update story status: {e}")

    def add_comment(self, story_id: str, content: str) -> bool:
        """Add comment to story.

        Args:
            story_id: Story ID
            content: Comment content

        Returns:
            True if successful

        Note:
            This is a placeholder - actual implementation needs proper POST handling
        """
        print(f"[TAPD] Add comment to story {story_id}: {content}")
        return True

    def create_story(
        self,
        name: str,
        description: str = "",
        owner: str = "",
        priority: str = "3",
        version: str = "",
    ) -> Dict[str, Any]:
        """Create new story.

        Args:
            name: Story name
            description: Story description
            owner: Story owner
            priority: Priority (1-4, default 3)
            version: Target version

        Returns:
            Created story data

        Note:
            This is a placeholder - actual implementation needs proper POST handling
        """
        print(f"[TAPD] Create story: {name}")
        print(f"  Owner: {owner}, Priority: {priority}, Version: {version}")
        return {"id": "placeholder", "name": name}


def get_tapd_client() -> TAPDClient:
    """Get TAPD client instance."""
    return TAPDClient()
