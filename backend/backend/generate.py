"""Pipeline orchestration endpoint combining research, synthesis, and images."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.graph import run_workflow, stream_workflow
from backend.images import ImageRequest, get_images as perform_images
from backend.openai_client import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_IMAGE_MODEL,
    has_valid_key,
)
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
    variants: int = Field(default=1, ge=1, le=6)
    images_per_prompt: int = Field(default=1, ge=1, le=4)
    mode: str = Field(default="full", pattern=r"^(full|prompts-only)$")

    # Multi-agent parameters
    use_agents: bool = Field(default=False, description="Use multi-agent system instead of linear pipeline")
    visual_references: list[str] = Field(default=[], description="Base64 encoded images or URLs")
    max_iterations: int = Field(default=3, ge=1, le=5, description="Max refinement iterations")

    # Research parameters (legacy)
    research_model: str = Field(default=DEFAULT_CHAT_MODEL)
    research_mode: str = Field(default="quick")
    reasoning_effort: str = Field(default="auto")

    # Synthesis parameters (legacy)
    synthesis_mode: str = Field(default="creative")

    # Image parameters
    image_model: str = Field(default=DEFAULT_IMAGE_MODEL)
    image_quality: str = Field(default="standard")
    image_size: str = Field(default="1024x1024")


@router.post("/generate")
def generate(req: GenerateRequest) -> dict[str, Any]:
    """Run the complete pipeline (legacy or multi-agent)."""
    if not has_valid_key():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )

    # Use multi-agent system if requested
    if req.use_agents:
        return _generate_with_agents(req)
    
    # Otherwise, use legacy linear pipeline
    return _generate_legacy(req)


def _generate_legacy(req: GenerateRequest) -> dict[str, Any]:
    """Legacy linear pipeline (Research → Synthesis → Images)."""
    research_req = ResearchRequest(
        topic=req.topic,
        audience=req.audience,
        age=req.age,
        research_mode=req.research_mode,
        model=req.research_model,
        reasoning_effort=req.reasoning_effort,
    )
    research_result: ResearchResponse = perform_research(research_req)

    synth_req = SynthesisRequest(
        research_text=research_result.analysis,
        audience=req.audience,
        age=req.age,
        variants=req.variants,
        synthesis_mode=req.synthesis_mode,
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


def _generate_with_agents(req: GenerateRequest) -> dict[str, Any]:
    """Multi-agent system pipeline."""
    try:
        # Run the multi-agent workflow
        final_state = run_workflow(
            user_brief=req.topic,
            audience=req.audience,
            age=req.age,
            visual_references=req.visual_references,
            variants=req.variants,
            images_per_prompt=req.images_per_prompt,
            image_model=req.image_model,
            image_quality=req.image_quality,
            image_size=req.image_size,
            max_iterations=req.max_iterations,
        )
        
        # Generate images if mode is "full"
        images_result: list[Any] = []
        if req.mode == "full":
            for prompt in final_state.get("current_prompts", []):
                if not prompt.get("positive"):
                    continue
                image_req = ImageRequest(
                    prompt_positive=prompt["positive"],
                    prompt_negative=prompt.get("negative", []),
                    n=req.images_per_prompt,
                    model=req.image_model,
                    quality=req.image_quality,
                    size=req.image_size,
                )
                try:
                    image_payload = perform_images(image_req)
                except HTTPException as exc:
                    logger.error("Image generation failed: %s", exc.detail)
                    images_result.append([{"error": exc.detail}])
                else:
                    images_result.append(image_payload.get("data", []))
        
        # Format response to match legacy structure
        return {
            "agent_system": {
                "vision_analysis": final_state.get("vision_analysis", ""),
                "style_context": final_state.get("style_context", []),
                "master_strategy": final_state.get("master_strategy", ""),
                "critique_score": final_state.get("critique_score", 0.0),
                "iteration_count": final_state.get("iteration_count", 0),
            },
            "prompts": final_state.get("current_prompts", []),
            "images": images_result,
        }
        
    except Exception as e:
        logger.error(f"Multi-agent workflow failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-agent workflow failed: {str(e)}",
        )


@router.post("/generate/stream")
async def generate_stream(req: GenerateRequest):
    """Stream the multi-agent workflow execution via Server-Sent Events."""
    if not has_valid_key():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )
    
    if not req.use_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is only available with use_agents=true",
        )
    
    async def event_generator():
        """Generate SSE events for each agent step."""
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting multi-agent workflow...'})}\n\n"
            
            # Stream workflow execution
            for node_name, state in stream_workflow(
                user_brief=req.topic,
                audience=req.audience,
                age=req.age,
                visual_references=req.visual_references,
                variants=req.variants,
                images_per_prompt=req.images_per_prompt,
                image_model=req.image_model,
                image_quality=req.image_quality,
                image_size=req.image_size,
                max_iterations=req.max_iterations,
            ):
                # Map node names to friendly agent names
                agent_map = {
                    "vision": "Agent-Vision",
                    "historian": "Agent-Historian",
                    "analyst": "Agent-Analyst",
                    "promptsmith": "Agent-Promptsmith",
                    "critic": "Agent-Critic",
                    "increment": "System",
                }
                
                agent_name = agent_map.get(node_name, node_name)
                
                # Build event data
                event_data = {
                    "type": "agent_step",
                    "agent": node_name,
                    "agent_name": agent_name,
                    "status": "completed",
                }
                
                # Add relevant data based on agent
                if node_name == "vision" and state.get("vision_analysis"):
                    event_data["data"] = {
                        "message": f"{agent_name} completed image analysis",
                        "analysis": state["vision_analysis"][:200] + "...",
                    }
                elif node_name == "historian":
                    count = len(state.get("style_context", []))
                    event_data["data"] = {
                        "message": f"{agent_name} found {count} similar styles",
                        "count": count,
                    }
                elif node_name == "analyst" and state.get("master_strategy"):
                    event_data["data"] = {
                        "message": f"{agent_name} created master strategy",
                        "strategy": state["master_strategy"][:200] + "...",
                    }
                elif node_name == "promptsmith":
                    count = len(state.get("current_prompts", []))
                    iteration = state.get("iteration_count", 0)
                    msg = f"{agent_name} generated {count} prompt(s)"
                    if iteration > 0:
                        msg += f" (iteration {iteration})"
                    event_data["data"] = {
                        "message": msg,
                        "count": count,
                        "iteration": iteration,
                    }
                elif node_name == "critic":
                    score = state.get("critique_score", 0.0)
                    decision = "APPROVED" if score >= 7.0 else "REJECTED"
                    event_data["data"] = {
                        "message": f"{agent_name} {decision} (score: {score}/10)",
                        "score": score,
                        "decision": decision,
                    }
                
                yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Workflow completed'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


__all__ = ["router", "GenerateRequest", "generate", "generate_stream"]

