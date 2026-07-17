#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TAPD API client."""

import json
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pathlib import Path
import yaml


class TAPDClient:
    """TAPD API client."""

    @staticmethod
    def get_short_id(story_id):
        """Extract short ID from full story ID.

        Args:
            story_id: Full story ID (e.g., "1135238004001009034") or short ID (e.g., "1009034")

        Returns:
            Short ID (last 7 digits)

        Examples:
            "1135238004001009034" -> "1009034"
            "1009034" -> "1009034"
        """
        story_id = str(story_id)
        if len(story_id) > 7:
            return story_id[-7:]
        return story_id

    def __init__(self, max_retries=3, retry_delay=1):
        """Initialize TAPD client.

        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay in seconds between retries
        """
        # Load config
        config_path = Path(__file__).parent.parent / "config" / "tapd_config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.base_url = config["tapd"]["base_url"].rstrip("/")
        self.workspace_id = config["tapd"]["workspace_id"]
        self.status_map = config["tapd"]["status_map"]
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Get token: first try user config, then environment variable
        self.token = None

        # Try to load from user config
        try:
            user_config_path = Path(__file__).parent.parent / "config" / "user_config.yaml"
            if user_config_path.exists():
                with open(user_config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config and "user" in user_config:
                        self.token = user_config["user"].get("tapd_token")
        except Exception:
            pass  # Ignore errors when loading user config

        # Fallback to environment variable
        if not self.token:
            token_env = config["tapd"]["token_env"]
            self.token = os.getenv(token_env)

        if not self.token:
            token_env = config["tapd"]["token_env"]
            raise ValueError(f"TAPD token not found. Set {token_env} environment variable or configure it during initialization.")

    def _request(self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET") -> List[Dict[str, Any]]:
        """Make HTTP request to TAPD API with retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method

        Returns:
            API response data

        Raises:
            RuntimeError: If request fails after all retries
        """
        params = params or {}
        params["workspace_id"] = self.workspace_id

        url = f"{self.base_url}{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"

        headers = {"Authorization": f"Bearer {self.token}"}

        last_error = None
        for attempt in range(self.max_retries):
            try:
                request = Request(url, headers=headers, method=method)
                with urlopen(request, timeout=30) as response:
                    payload = json.load(response)

                if payload.get("status") != 1:
                    raise RuntimeError(f"TAPD API error: {payload.get('info')}")

                return payload.get("data", [])

            except HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code in [500, 502, 503, 504]:  # Server errors, retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                raise RuntimeError(f"TAPD API HTTP error: {last_error}")

            except URLError as e:
                last_error = f"Network error: {e.reason}"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise RuntimeError(f"TAPD API network error: {last_error}")

            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise RuntimeError(f"TAPD API error: {last_error}")

        raise RuntimeError(f"TAPD API request failed after {self.max_retries} attempts: {last_error}")

    def normalize_story_id(self, story_id: str) -> str:
        """Normalize story ID - convert short ID to full ID if needed.

        Args:
            story_id: Short ID (7 digits) or full ID (19 digits)

        Returns:
            Full story ID (19 digits)

        Raises:
            ValueError: If story ID format is invalid or story not found
        """
        story_id = story_id.strip()

        # If already full ID (19 digits), return as is
        if len(story_id) == 19 and story_id.isdigit():
            return story_id

        # If short ID (7 digits or less), query to find full ID
        if len(story_id) <= 7 and story_id.isdigit():
            # Try to construct full ID using workspace_id prefix
            # TAPD story ID format: {workspace_id}{story_number}
            # For workspace 1135238004, the full ID would be: 1135238004 + 00 + short_id
            potential_full_id = f"{self.workspace_id}00{story_id}"

            # Try direct lookup first
            try:
                data = self._request("/stories", params={"id": potential_full_id})
                if data:
                    return potential_full_id
            except:
                pass

            # If direct lookup fails, search through all stories
            # This is slower but more reliable
            stories = self.query_stories(limit=1000)
            for story in stories:
                full_id = story.get('id', '')
                if full_id.endswith(story_id):
                    return full_id

            raise ValueError(f"Story not found with short ID: {story_id}")

        # Invalid format
        raise ValueError(f"Invalid story ID format: {story_id}. Expected 7-digit short ID or 19-digit full ID")

    def get_story_detail(self, story_id: str) -> Dict[str, Any]:
        """Get story details by ID.

        Args:
            story_id: Short ID (7 digits) or full ID (19 digits)

        Returns:
            Story details dict

        Raises:
            ValueError: If story not found
        """
        # Normalize to full ID
        full_id = self.normalize_story_id(story_id)
        data = self._request("/stories", params={"id": full_id})
        if not data:
            raise ValueError(f"Story not found: {story_id}")
        return data[0].get("Story", {})

    def query_stories(
        self,
        version: str = None,
        owner: str = None,
        status: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query stories with filters."""
        params = {"limit": limit}
        if version:
            params["version"] = version
        if owner:
            params["owner"] = owner
        if status:
            params["status"] = status

        data = self._request("/stories", params=params)
        return [item.get("Story", {}) for item in data]

    def update_story_status(self, story_id: str, status: str, comment: str = None) -> Dict[str, Any]:
        """Update story status.

        Args:
            story_id: Short ID (7 digits) or full ID (19 digits)
            status: New status (e.g., 'developing', 'resolved', 'status_6')
            comment: Optional comment

        Returns:
            Updated story data
        """
        # Normalize to full ID
        full_id = self.normalize_story_id(story_id)

        # Prepare form data
        data = {
            'workspace_id': self.workspace_id,
            'id': full_id,
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
            result = payload.get('data', {})
            if result:
                return result.get('Story', {})
            return {}
        except Exception as e:
            raise RuntimeError(f"Failed to update story status: {e}")
