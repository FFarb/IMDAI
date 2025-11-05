"""Image generation endpoint for the three-stage pipeline."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.openai_client import (
    ALLOW_TRUE_GRADIENTS,
    GPT_IMAGE_MODEL,
    get_openai_client,
    has_valid_key,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


class ImageRequest(BaseModel):
    """Input payload for requesting generated images."""

    prompt_positive: str
    prompt_negative: list[str] = Field(default_factory=list)
    n: int = Field(default=1, ge=1, le=4)


class ImageResponse(BaseModel):
    """Normalised response payload for generated images."""

    data: list[dict[str, Any]]


def _build_negative_terms(base_terms: list[str]) -> list[str]:
    """Derive the negative prompt terms with gradient policy applied."""

    negatives = list(base_terms)
    if not ALLOW_TRUE_GRADIENTS:
        for term in ("gradients", "textures"):
            if term not in negatives:
                negatives.append(term)
    return negatives


@router.post("/images", response_model=ImageResponse)
def get_images(req: ImageRequest) -> dict[str, Any]:
    """Generate images using the configured OpenAI image model."""

    if not has_valid_key():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )

    client = get_openai_client()
    if client is None:  # pragma: no cover - defensive path
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )

    negatives = _build_negative_terms(req.prompt_negative)
    avoid_clause = f" --no {', '.join(negatives)}" if negatives else ""
    full_prompt = f"{req.prompt_positive}{avoid_clause}"

    try:
        response = client.images.generate(
            model=GPT_IMAGE_MODEL,
            prompt=full_prompt,
            size="1024x1024",
            quality="auto",
            n=req.n,
        )
    except Exception as exc:  # pragma: no cover - network failure path
        logger.error("Image generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image generation failed",
        )

    items = []
    for item in getattr(response, "data", []) or []:
        entry = {
            "url": getattr(item, "url", None),
            "b64_json": getattr(item, "b64_json", None),
        }
        if any(entry.values()):
            items.append(entry)

    if not items:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image API returned no data",
        )

    return {"data": items}


__all__ = ["router", "ImageRequest", "get_images"]
