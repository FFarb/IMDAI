"""Generic image search adapter using a configurable API."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = os.getenv("GENERIC_SEARCH_ENDPOINT", "")


class GenericAdapter:
    """Fetch image references from a generic provider."""

    name = "generic"

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GENERIC_SEARCH_KEY")
        self.endpoint = endpoint or DEFAULT_ENDPOINT

    async def search(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Query the configured generic image search endpoint."""
        if not query or not self.api_key or not self.endpoint:
            logger.debug("Generic adapter disabled due to missing configuration")
            return []

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"q": query, "limit": limit}
        try:
            response = await client.get(self.endpoint, params=params, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failures
            logger.warning("Generic provider request failed: %s", exc)
            return []

        payload = response.json()
        items = payload.get("results", [])
        results: List[Dict[str, Any]] = []
        for item in items:
            thumb = item.get("thumbnail") or item.get("thumb_url") or item.get("image")
            url = item.get("url") or item.get("image_url")
            if not thumb or not url:
                continue
            results.append(
                {
                    "site": self.name,
                    "url": url,
                    "thumb_url": thumb,
                    "title": item.get("title"),
                    "license": item.get("license"),
                    "author": item.get("source") or item.get("author"),
                    "width": item.get("width"),
                    "height": item.get("height"),
                }
            )
            if len(results) >= limit:
                break
        return results
