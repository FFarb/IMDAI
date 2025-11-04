"""Pipeline orchestration endpoint combining research, synthesis, and images."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.openai_client import has_valid_key
from backend.images import ImageRequest, get_images as perform_images
from backend.research import ResearchRequest, research as perform_research
from backend.synthesize import SynthesisRequest, synthesize as perform_synthesis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pipeline"])


class GenerateRequest(BaseModel):
    """Full pipeline input payload."""

    topic: str
    audience: str
    age: str | None = None
    depth: int = Field(default=1, ge=1, le=5)
    variants: int = Field(default=1, ge=1, le=6)
    images_per_prompt: int = Field(default=1, ge=1, le=4)
    mode: str = Field(default="full", pattern=r"^(full|prompts-only)$")


@router.post("/generate")
def generate(req: GenerateRequest) -> dict[str, Any]:
    """Run the complete three-stage pipeline or produce prompts only."""

    if not has_valid_key():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )

    research_req = ResearchRequest(
        topic=req.topic,
        audience=req.audience,
        age=req.age,
        depth=req.depth,
    )
    research_result = perform_research(research_req)

    synth_req = SynthesisRequest(
        research=research_result,
        audience=req.audience,
        age=req.age,
        variants=req.variants,
    )
    synthesis_result = perform_synthesis(synth_req)

    images_result: list[Any] = []
    if req.mode == "full":
        for prompt in synthesis_result.get("prompts", []):
            positive = prompt.get("positive", "")
            if not positive:
                continue
            negative_terms = prompt.get("negative") or []
            image_req = ImageRequest(
                prompt_positive=positive,
                prompt_negative=list(negative_terms),
                n=req.images_per_prompt,
            )
            try:
                image_payload = perform_images(image_req)
            except HTTPException as exc:
                logger.error("Image generation failed during orchestration: %s", exc.detail)
                images_result.append([{"error": exc.detail}])
            else:
                images_result.append(image_payload.get("data", []))

    return {
        "research": research_result,
        "synthesis": synthesis_result,
        "images": images_result,
    }


__all__ = ["router", "GenerateRequest", "generate"]
