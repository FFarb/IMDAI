"""Thumbnail normalization utilities."""
from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional, Tuple

import httpx
from PIL import Image

THUMBS_DIR = Path("data/discovery/thumbs")
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

THUMBNAIL_SIZE = 240
DEFAULT_MIME = "image/webp"


class ThumbnailError(Exception):
    """Raised when thumbnail processing fails."""


def _decode_data_url(url: str) -> Tuple[bytes, str]:
    try:
        header, encoded = url.split(",", 1)
    except ValueError as exc:  # pragma: no cover - malformed data URL
        raise ThumbnailError("Invalid data URL") from exc
    mime_part = header.split(";")[0]
    mime = mime_part[5:] if mime_part.startswith("data:") else "image/jpeg"
    return base64.b64decode(encoded), mime


async def fetch_source(
    url: str,
    client: Optional[httpx.AsyncClient],
) -> Tuple[bytes, str]:
    """Fetch thumbnail bytes either from data URL or remote HTTP."""
    if url.startswith("data:"):
        return _decode_data_url(url)
    if client is None:
        raise ThumbnailError("HTTP client required for remote thumbnail fetch")
    response = await client.get(url, timeout=8.0, follow_redirects=True)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image"):
        raise ThumbnailError(f"Unsupported content type: {content_type}")
    mime = content_type.split(";")[0]
    return response.content, mime


def normalize_image(data: bytes, mime: Optional[str] = None) -> Tuple[bytes, str, Image.Image]:
    """Resize and encode an image to a standardized thumbnail."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            image = img.convert("RGB")
    except Exception as exc:  # pragma: no cover - Pillow errors
        raise ThumbnailError("Failed to decode image") from exc

    width, height = image.size
    if min(width, height) > THUMBNAIL_SIZE:
        if width <= height:
            new_width = THUMBNAIL_SIZE
            new_height = int(height * (THUMBNAIL_SIZE / width))
        else:
            new_height = THUMBNAIL_SIZE
            new_width = int(width * (THUMBNAIL_SIZE / height))
        image = image.resize((max(1, new_width), max(1, new_height)), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=75, method=6)
    payload = buffer.getvalue()
    preview = image.copy()
    return payload, DEFAULT_MIME, preview


def store_thumbnail(reference_id: str, data: bytes) -> str:
    """Persist thumbnail bytes and return the public URL."""
    path = thumbnail_path(reference_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return f"/api/discover/thumb/{reference_id}"


def thumbnail_path(reference_id: str) -> Path:
    """Return the filesystem path for a stored thumbnail."""
    return THUMBS_DIR / f"{reference_id}.webp"
