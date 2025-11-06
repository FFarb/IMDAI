"""Pipeline orchestration endpoint combining research, synthesis, and images."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.openai_client import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_IMAGE_MODEL,
    has_valid_key,
)
from backend.images import ImageRequest, get_images as perform_images
from backend.research import ResearchRequest, ResearchResponse, research as perform_research
from backend.synthesize import (
    SynthesisRequest,
    SynthesisResponse,
    synthesize as perform_synthesis,
)

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

    # Research parameters
    research_model: str = Field(default=DEFAULT_CHAT_MODEL)
    reasoning_effort: str = Field(default="auto")

    # Image parameters
    image_model: str = Field(default=DEFAULT_IMAGE_MODEL)
    image_quality: str = Field(default="standard")
    image_size: str = Field(default="1024x1024")


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
        model=req.research_model,
        reasoning_effort=req.reasoning_effort,
    )
    research_result: ResearchResponse = perform_research(research_req)

    synth_req = SynthesisRequest(
        research_text=research_result.analysis,
        audience=req.audience,
        age=req.age,
        variants=req.variants,
    )
    synthesis_result: SynthesisResponse = perform_synthesis(synth_req)

    images_result: list[Any] = []
    if req.mode == "full":
        for prompt in synthesis_result.prompts:
            if not prompt.positive:
                continue
            image_req = ImageRequest(
                prompt_positive=prompt.positive,
                prompt_negative=list(prompt.negative),
                n=req.images_per_prompt,
                model=req.image_model,
                quality=req.image_quality,
                size=req.image_size,
            )
            try:
                image_payload = perform_images(image_req)
            except HTTPException as exc:
                logger.error("Image generation failed during orchestration: %s", exc.detail)
                images_result.append([{"error": exc.detail}])
            else:
                images_result.append(image_payload.get("data", []))

    return {
        "research": research_result.model_dump(),
        "synthesis": synthesis_result.model_dump(),
        "images": images_result,
    }


__all__ = ["router", "GenerateRequest", "generate"]
