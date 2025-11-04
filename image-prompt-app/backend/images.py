from __future__ import annotations

import logging
from typing import Any, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from openai_client import ALLOW_TRUE_GRADIENTS, GPT_IMAGE_MODEL, get_openai_client, has_valid_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


# ----- Pydantic Models ---------------------------------------------------------

class ImageRequest(BaseModel):
    prompt_positive: str
    prompt_negative: List[str] = Field(default_factory=list)
    n: int = Field(default=1, ge=1, le=4)


class ImageResponse(BaseModel):
    images: List[dict[str, Any]]


# ----- Route -------------------------------------------------------------------

@router.post("/images", response_model=ImageResponse)
def get_images(req: ImageRequest) -> dict[str, Any]:
    """Generates images based on a positive and negative prompt."""
    if not has_valid_key():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    client = get_openai_client()
    if not client:
        # This case should be covered by has_valid_key, but as a fallback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    negatives = list(req.prompt_negative)  # Make a mutable copy
    if not ALLOW_TRUE_GRADIENTS:
        # Enforce vector safety if the environment flag is set to false
        for term in ["gradients", "textures", "photorealism"]:
            if term not in negatives:
                negatives.append(term)

    avoid_clause = f" --no {', '.join(negatives)}" if negatives else ""
    full_prompt = f"{req.prompt_positive}{avoid_clause}"

    try:
        response = client.images.generate(
            model=GPT_IMAGE_MODEL,
            prompt=full_prompt,
            size="1024x1024",  # Using a common, fast size
            quality="standard",
            n=req.n,
        )
    except Exception as exc:
        logger.error(f"Image generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Image generation API call failed: {exc}")

    images_data = []
    if response.data:
        for item in response.data:
            if item.url:
                images_data.append({"url": item.url})
            elif item.b64_json:
                images_data.append({"b64_json": item.b64_json})

    if not images_data:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Image API returned no data")

    return {"images": images_data}
