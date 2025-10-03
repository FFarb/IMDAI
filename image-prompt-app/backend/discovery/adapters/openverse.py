"""Adapter for the Openverse API."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

OPENVERSE_API_URL = "https://api.openverse.engineering/v1/images/"
DEFAULT_PAGE_SIZE = 50


class OpenverseAdapter:
    """Fetch image references from Openverse."""

    name = "openverse"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENVERSE_KEY")

    async def search(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Query Openverse for image references."""
        if not query:
            return []

        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        results: List[Dict[str, Any]] = []
        page = 1
        page_size = max(1, min(DEFAULT_PAGE_SIZE, limit))

        while len(results) < limit:
            params = {
                "q": query,
                "page": page,
                "page_size": page_size,
                "license_type": "all",
                "mature": "false",
            }
            try:
                response = await client.get(OPENVERSE_API_URL, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:  # pragma: no cover - network failures
                logger.warning("Openverse request failed: %s", exc)
                break

            payload = response.json()
            items = payload.get("results", [])
            if not items:
                break

            for item in items:
                thumb = item.get("thumbnail") or item.get("url")
                url = item.get("url") or item.get("foreign_landing_url")
                if not thumb or not url:
                    continue
                results.append(
                    {
                        "site": self.name,
                        "url": url,
                        "thumb_url": thumb,
                        "title": item.get("title"),
                        "license": item.get("license"),
                        "author": item.get("creator"),
                        "width": item.get("width"),
                        "height": item.get("height"),
                    }
                )
                if len(results) >= limit:
                    break
            page += 1
        return results[:limit]
