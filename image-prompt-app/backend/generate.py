from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from openai_client import get_openai_client, has_valid_key
from prompts import RESEARCH_SYSTEM, RESEARCH_USER, SYNTH_SYSTEM, SYNTH_USER
from schemas import RESEARCH_SCHEMA, SYNTHESIS_SCHEMA

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pipeline"])


# ----- Pydantic payload shapes -------------------------------------------------
class ReferenceItem(BaseModel):
    url: str
    title: str
    type: Literal["gallery", "article", "store", "blog", "community", "other"]
    summary: Optional[str] = None


class PaletteItem(BaseModel):
    hex: str
    weight: float


class ResearchPayload(BaseModel):
    references: List[ReferenceItem]
    motifs: List[str]
    composition: List[str]
    line: Literal["ultra-thin", "thin", "regular", "bold"]
    outline: Literal["none", "clean", "heavy", "rough"]
    typography: List[str]
    palette: List[PaletteItem]
    mood: Optional[List[str]] = None
    hooks: Optional[List[str]] = None
    notes: Optional[str] = None


class SynthPrompt(BaseModel):
    title: Optional[str] = None
    positive: str
    negative: List[str]
    notes: Optional[str] = None


class SynthesisPayload(BaseModel):
    prompts: List[SynthPrompt]


class GenerateRequest(BaseModel):
    topic: str
    audience: str
    age: str
    depth: int = Field(ge=1, le=5, default=3)
    variants: int = Field(ge=1, le=5, default=2)
    images_per_prompt: int = Field(ge=1, le=4, default=1)
    mode: str = Field(pattern="^(full|research_only|synthesis_only|images_only)$", default="full")
    selected_prompt_index: Optional[int] = None
    research: Optional[ResearchPayload] = None
    synthesis: Optional[SynthesisPayload] = None


# ----- Helpers -----------------------------------------------------------------
def _responses_call(messages: List[Dict[str, Any]], json_schema: Dict[str, Any], *, use_web: bool) -> Dict[str, Any]:
    client = get_openai_client()
    if not client:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OPENAI_API_KEY not configured")

    payload: Dict[str, Any] = {
        "model": "gpt-4.1-nano",
        "input": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "contract", "schema": json_schema, "strict": True},
        },
    }
    if use_web:
        payload["tools"] = [{"type": "web_search"}]
        payload["tool_choice"] = "auto"

    try:
        response = client.responses.create(**payload)
    except Exception as exc:  # pragma: no cover - network error path
        logger.error("Responses API failure: %s", exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Responses API call failed") from exc

    text = getattr(response, "output_text", None)
    if not text:
        parts: List[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text_value = getattr(content, "text", None)
                if isinstance(text_value, str):
                    parts.append(text_value)
        text = "".join(parts).strip()
    if not text:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Empty output from Responses API")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
        logger.error("Failed to decode JSON response: %s", text)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Invalid JSON from model: {exc}") from exc


def research_step(topic: str, audience: str, age: str, depth: int) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": [{"type": "input_text", "text": RESEARCH_SYSTEM}]},
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": RESEARCH_USER.format(topic=topic, audience=audience, age=age, depth=depth),
                }
            ],
        },
    ]
    return _responses_call(messages, RESEARCH_SCHEMA, use_web=True)


def synthesis_step(research_json: Dict[str, Any], audience: str, age: str, variants: int) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "input_text", "text": SYNTH_SYSTEM.format(max_variants=variants)},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": SYNTH_USER.format(
                        RESEARCH_JSON=json.dumps(research_json, ensure_ascii=False),
                        audience=audience,
                        age=age,
                        variants=variants,
                    ),
                }
            ],
        },
    ]
    return _responses_call(messages, SYNTHESIS_SCHEMA, use_web=False)


def image_step(positive: str, negatives: List[str], n: int) -> List[Dict[str, Any]]:
    client = get_openai_client()
    if not client:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OPENAI_API_KEY not configured")

    avoid_clause = f"\n\nAvoid: {', '.join(negatives)}" if negatives else ""
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=f"{positive}{avoid_clause}",
            size="1536x1024",
            quality="low",
            n=n,
        )
    except Exception as exc:  # pragma: no cover - network error path
        logger.error("Images API failure: %s", exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Images API call failed") from exc

    images: List[Dict[str, Any]] = []
    for item in getattr(response, "data", []) or []:
        url = getattr(item, "url", None)
        b64_json = getattr(item, "b64_json", None)
        if url:
            images.append({"url": url})
        elif b64_json:
            images.append({"b64_json": b64_json})
    if not images:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Images API returned no data")
    return images


# ----- Route -------------------------------------------------------------------
@router.post("/generate")
def generate(req: GenerateRequest) -> Dict[str, Any]:
    if not has_valid_key():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OPENAI_API_KEY not configured")

    research_result: Optional[Dict[str, Any]] = req.research.model_dump() if req.research else None
    synthesis_result: Optional[Dict[str, Any]] = req.synthesis.model_dump() if req.synthesis else None
    images_result: Optional[List[List[Dict[str, Any]]]] = None

    mode = req.mode

    if mode == "research_only":
        research_result = research_step(req.topic, req.audience, req.age, req.depth)
        return {"research": research_result, "synthesis": None, "images": None}

    if mode == "synthesis_only":
        if research_result is None:
            research_result = research_step(req.topic, req.audience, req.age, req.depth)
        synthesis_result = synthesis_step(research_result, req.audience, req.age, req.variants)
        return {"research": research_result, "synthesis": synthesis_result, "images": None}

    if mode == "images_only":
        if synthesis_result is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Synthesis data required for images_only mode")
        index = req.selected_prompt_index or 0
        prompts = synthesis_result.get("prompts", [])
        if index < 0 or index >= len(prompts):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "selected_prompt_index out of range")
        prompt = prompts[index]
        images = image_step(prompt.get("positive", ""), prompt.get("negative", []), req.images_per_prompt)
        images_result = [images]
        return {"research": research_result, "synthesis": synthesis_result, "images": images_result}

    # full pipeline
    research_result = research_step(req.topic, req.audience, req.age, req.depth)
    synthesis_result = synthesis_step(research_result, req.audience, req.age, req.variants)
    images_result = []
    for prompt in synthesis_result.get("prompts", []):
        images_result.append(image_step(prompt.get("positive", ""), prompt.get("negative", []), req.images_per_prompt))

    return {"research": research_result, "synthesis": synthesis_result, "images": images_result}
