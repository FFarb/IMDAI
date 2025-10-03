"""Adapter for the Unsplash API."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
MAX_PER_PAGE = 30
LICENSE = "Unsplash License"


class UnsplashAdapter:
    """Fetch image references from Unsplash."""

    name = "unsplash"

    def __init__(self, access_key: Optional[str] = None) -> None:
        self.access_key = access_key or os.getenv("UNSPLASH_KEY")

    async def search(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Query Unsplash for image references."""
        if not query or not self.access_key:
            return []

        headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {self.access_key}"}
        results: List[Dict[str, Any]] = []
        page = 1
        per_page = max(1, min(MAX_PER_PAGE, limit))

        while len(results) < limit:
            params = {"query": query, "page": page, "per_page": per_page}
            try:
                response = await client.get(UNSPLASH_API_URL, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:  # pragma: no cover - network failures
                logger.warning("Unsplash request failed: %s", exc)
                break

            payload = response.json()
            items = payload.get("results", [])
            if not items:
                break

            for item in items:
                urls = item.get("urls", {})
                links = item.get("links", {})
                thumb = urls.get("small") or urls.get("thumb")
                url = links.get("html") or item.get("links", {}).get("download")
                if not thumb or not url:
                    continue
                author = item.get("user", {}).get("name")
                results.append(
                    {
                        "site": self.name,
                        "url": url,
                        "thumb_url": thumb,
                        "title": item.get("description") or item.get("alt_description"),
                        "license": LICENSE,
                        "author": author,
                        "width": item.get("width"),
                        "height": item.get("height"),
                    }
                )
                if len(results) >= limit:
                    break
            page += 1
        return results[:limit]
