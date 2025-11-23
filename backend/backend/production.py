"""Production endpoints for upscaling and vectorizing."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.tools.upscaler import Upscaler
from backend.tools.vectorizer import Vectorizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/production", tags=["production"])


class ProductionRequest(BaseModel):
    """Request to process an image."""
    image_path: str


@router.post("/upscale")
def upscale_image(req: ProductionRequest) -> dict[str, str]:
    """Upscale an image."""
    try:
        upscaler = Upscaler()
        input_path = Path(req.image_path)
        output_path = input_path.parent / "master.png"
        
        result = upscaler.upscale(input_path, output_path)
        return {"path": str(result), "url": f"/files/{result.name}"} # Assuming static file serving or similar
    except Exception as e:
        logger.error(f"Upscaling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectorize")
def vectorize_image(req: ProductionRequest) -> dict[str, str]:
    """Vectorize an image."""
    try:
        vectorizer = Vectorizer()
        input_path = Path(req.image_path)
        output_path = input_path.parent / "vector.svg"
        
        result = vectorizer.vectorize(input_path, output_path)
        return {"path": str(result), "url": f"/files/{result.name}"}
    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
