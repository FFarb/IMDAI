"""Image generation endpoint for the three-stage pipeline."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.openai_client import (
    ALLOW_TRUE_GRADIENTS,
    DEFAULT_IMAGE_MODEL,
    get_openai_client,
    has_valid_key,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])

# Constraint dictionaries for DALL-E models
DALLE2_CONSTRAINTS = {
    "max_prompt_chars": 1000,
    "qualities": {"standard"},
    "sizes": {"256x256", "512x512", "1024x1024"},
}
DALLE3_CONSTRAINTS = {
    "max_prompt_chars": 4000,
    "qualities": {"standard", "hd"},
    "sizes": {"1024x1024", "1792x1024", "1024x1792"},
}
SUPPORTED_MODELS = {
    "dall-e-2": DALLE2_CONSTRAINTS,
    "dall-e-3": DALLE3_CONSTRAINTS,
}


class ImageRequest(BaseModel):
    """Input payload for requesting generated images."""

    prompt_positive: str
    prompt_negative: list[str] = Field(default_factory=list)
    n: int = Field(default=1, ge=1, le=4)
    model: str = Field(default=DEFAULT_IMAGE_MODEL)
    quality: str = Field(default="standard")
    size: str = Field(default="1024x1024")


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
    # Step A: Get Client
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

    # Step B: Determine Model Key
    model_key = req.model.lower()
    if model_key not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported model: {req.model}",
        )
    constraints = SUPPORTED_MODELS[model_key]

    # Step C: Validation (Quality)
    if req.quality not in constraints["qualities"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Quality '{req.quality}' not supported for model '{req.model}'",
        )

    # Step D: Validation (Size)
    if req.size not in constraints["sizes"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Size '{req.size}' not supported for model '{req.model}'",
        )

    # Step E: Build and Truncate Prompt
    negatives = _build_negative_terms(req.prompt_negative)
    avoid_clause = f" --no {', '.join(negatives)}" if negatives else ""
    full_prompt = f"{req.prompt_positive}{avoid_clause}"
    max_len = constraints["max_prompt_chars"]
    if len(full_prompt) > max_len:
        full_prompt = full_prompt[:max_len]
        logger.warning("Truncated prompt for model %s to %d chars.", model_key, max_len)

    try:
        # Step F: API Call
        response = client.images.generate(
            model=req.model,
            prompt=full_prompt,
            size=req.size,
            quality=req.quality,
            n=req.n,
            response_format='b64_json',  # Critical for autosave
        )
    except Exception as exc:  # pragma: no cover - network failure path
        logger.error("Image generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image generation failed",
        )

    # Step G: Response Parsing
    items = []
    for item in getattr(response, "data", []) or []:
        entry = {
            "url": getattr(item, "url", None),
            "b64_json": getattr(item, "b64_json", None),
            "revised_prompt": getattr(item, "revised_prompt", None),
        }
        if any(v for k, v in entry.items() if k != "revised_prompt"):
            items.append(entry)

    if not items:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image API returned no data",
        )

    return {"data": items}


__all__ = ["router", "ImageRequest", "get_images"]
