from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from research import research as perform_research
from research import ResearchRequest
from synthesize import synthesize as perform_synthesis
from synthesize import SynthesisRequest
from images import get_images as perform_images
from images import ImageRequest
from openai_client import has_valid_key


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["legacy"])


# ----- Pydantic Models ---------------------------------------------------------

class FullPipelineRequest(BaseModel):
    topic: str
    audience: str
    age: str
    depth: int = Field(default=3, ge=1, le=5)
    variants: int = Field(default=2, ge=1, le=5)
    images_per_prompt: int = Field(default=1, ge=1, le=4)


# ----- Route -------------------------------------------------------------------

@router.post("/generate", summary="Run the full research-synthesis-image pipeline")
def generate_full_pipeline(req: FullPipelineRequest) -> Dict[str, Any]:
    """
    An orchestrator endpoint that calls the research, synthesize, and image
    endpoints in sequence. This is a convenience wrapper for clients that
    want to perform the entire pipeline in a single call.
    """
    if not has_valid_key():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    # 1. Research Step
    try:
        research_req = ResearchRequest(topic=req.topic, audience=req.audience, age=req.age, depth=req.depth)
        research_result = perform_research(research_req)
    except HTTPException as exc:
        logger.error(f"Error in research step: {exc.detail}")
        raise HTTPException(status_code=exc.status_code, detail=f"Research step failed: {exc.detail}")

    # 2. Synthesis Step
    try:
        synth_req = SynthesisRequest(research=research_result, audience=req.audience, age=req.age, variants=req.variants)
        synthesis_result = perform_synthesis(synth_req)
    except HTTPException as exc:
        logger.error(f"Error in synthesis step: {exc.detail}")
        raise HTTPException(status_code=exc.status_code, detail=f"Synthesis step failed: {exc.detail}")

    # 3. Image Generation Step
    images_result = []
    prompts = synthesis_result.get("prompts", [])
    if not prompts:
        # If no prompts were generated, we can't create images.
        # This is a successful partial result.
        return {"research": research_result, "synthesis": synthesis_result, "images": []}

    for prompt in prompts:
        try:
            positive_prompt = prompt.get("positive", "")
            negative_prompt = prompt.get("negative", [])

            if not positive_prompt:
                continue

            image_req = ImageRequest(prompt_positive=positive_prompt, prompt_negative=negative_prompt, n=req.images_per_prompt)
            image_response = perform_images(image_req)
            images_result.append(image_response["images"])

        except HTTPException as exc:
            # Log the error but continue to the next prompt
            logger.error(f"Error generating images for a prompt: {exc.detail}")
            # Append an error marker or an empty list for this prompt's images
            images_result.append([{"error": f"Image generation failed: {exc.detail}"}])


    return {"research": research_result, "synthesis": synthesis_result, "images": images_result}
