"""Synthesis stage endpoint for converting research into prompts."""
from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.openai_client import GPT_SYNTH_MODEL, get_openai_client, has_valid_key
from backend.prompts import SYNTH_SYSTEM, SYNTH_USER
from backend.schemas import SYNTHESIS_SCHEMA
from backend.utils.json_sanitize import extract_json_text
from backend.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


class SynthesisPrompt(BaseModel):
    """Prompt returned by the synthesis stage."""

    positive: str
    negative: list[str]
    notes: str | None = None


class SynthesisResponse(BaseModel):
    """Response payload with parsed prompt variants."""

    prompts: list[SynthesisPrompt]
    raw_text: str


class SynthesisRequest(BaseModel):
    """Input payload for the synthesis step."""

    research_text: str
    audience: str
    age: str | None = None
    variants: int = Field(default=1, ge=1, le=6)


@retry_with_exponential_backoff()
def _create_synthesis_completion(client: Any, messages: list[dict[str, str]]) -> Any:
    """Invoke the OpenAI API and return the raw completion object."""

    return client.chat.completions.create(
        model=GPT_SYNTH_MODEL,
        messages=messages,
        temperature=0.7,
    )


def _render_synthesis_messages(req: SynthesisRequest) -> list[dict[str, str]]:
    audience_age = req.age or "all ages"
    system_prompt = SYNTH_SYSTEM.replace("$max_variants", str(req.variants))
    user_prompt = (
        SYNTH_USER.replace("$RESEARCH_TEXT", req.research_text)
        .replace("$audience", req.audience)
        .replace("$age", audience_age)
        .replace("$variants", str(req.variants))
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


PROMPT_BLOCK_RE = re.compile(
    r"^\s*PROMPT\s*(\d+)\s*:\s*(.*?)(?=^\s*PROMPT\s*\d+\s*:|\Z)", re.I | re.S | re.M
)


def _extract_section(block: str, title: str) -> str:
    pattern = re.compile(rf"{title}\s*[:\-]\s*(.*?)(?=\n[A-Z][\w\s]+[:\-]|\Z)", re.S)
    match = pattern.search(block)
    if match:
        return match.group(1).strip()
    return ""


def _parse_prompt_blocks(raw_text: str) -> list[SynthesisPrompt]:
    cleaned = extract_json_text(raw_text or "").replace("\ufeff", "").replace("\x00", "").strip()
    prompts: list[SynthesisPrompt] = []
    for match in PROMPT_BLOCK_RE.finditer(cleaned):
        block = match.group(2).strip()
        positive = _extract_section(block, "Positive") or block
        negative_section = _extract_section(block, "Negative")
        negative_terms = [term.strip() for term in re.split(r"[,\n]", negative_section) if term.strip()]
        notes = _extract_section(block, "Notes") or None
        prompts.append(SynthesisPrompt(positive=positive, negative=negative_terms, notes=notes))

    if not prompts and cleaned:
        prompts.append(SynthesisPrompt(positive=cleaned, negative=[]))

    return prompts


def _limit_prompts(prompts: list[SynthesisPrompt], count: int) -> list[SynthesisPrompt]:
    if count <= 0:
        return prompts
    return prompts[:count]


@router.post("/synthesize", response_model=SynthesisResponse)
def synthesize(req: SynthesisRequest) -> SynthesisResponse:
    """Generate image prompts from textual research insights."""

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

    messages = _render_synthesis_messages(req)

    try:
        response = _create_synthesis_completion(client, messages)
    except Exception as exc:  # pragma: no cover - retried failure
        logger.error("OpenAI synthesis completion failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM API call failed",
        )

    raw_text = getattr(response.choices[0].message, "content", "") if response.choices else ""
    cleaned = extract_json_text(raw_text or "").replace("\ufeff", "").replace("\x00", "").strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Empty output from model",
        )

    prompts = _limit_prompts(_parse_prompt_blocks(cleaned), req.variants)
    response_payload = SynthesisResponse(prompts=prompts, raw_text=cleaned)

    if SYNTHESIS_SCHEMA is not None:
        try:
            from jsonschema import validate as jsonschema_validate

            jsonschema_validate(instance=response_payload.model_dump(), schema=SYNTHESIS_SCHEMA)
        except Exception:  # pragma: no cover - advisory only
            logger.info("Synthesis payload deviated from advisory schema; continuing.")

    return response_payload


__all__ = [
    "router",
    "SynthesisRequest",
    "SynthesisResponse",
    "SynthesisPrompt",
    "synthesize",
]
