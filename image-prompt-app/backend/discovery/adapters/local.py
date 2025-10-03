"""Local upload adapter for reference discovery."""
from __future__ import annotations

import base64
import uuid
from typing import Any, Dict, List

from fastapi import UploadFile

MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB preview limit


class LocalAdapter:
    """Convert uploaded files into reference records."""

    name = "local"

    async def ingest(self, session_id: str, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Transform uploaded files into raw reference dictionaries."""
        references: List[Dict[str, Any]] = []
        for file in files:
            try:
                if not file.content_type or not file.content_type.startswith("image/"):
                    continue
                data = await file.read()
                if len(data) > MAX_FILE_SIZE:
                    raise ValueError(
                        f"File {file.filename} exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"
                    )
                encoded = base64.b64encode(data).decode("ascii")
                thumb_url = f"data:{file.content_type};base64,{encoded}"
                reference_id = str(uuid.uuid4())
                references.append(
                    {
                        "id": reference_id,
                        "session_id": session_id,
                        "site": self.name,
                        "url": f"local://{reference_id}",
                        "thumb_url": thumb_url,
                        "title": file.filename,
                        "license": None,
                        "author": None,
                        "width": None,
                        "height": None,
                    }
                )
            finally:
                await file.close()
        return references
