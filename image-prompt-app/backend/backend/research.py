"""Research stage endpoint for the three-stage design pipeline."""
from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.openai_client import (
    DEFAULT_CHAT_MODEL,
    get_openai_client,
    has_valid_key,
    is_reasoning_model,
)
from backend.prompts import RESEARCH_SYSTEM, RESEARCH_USER
from backend.schemas import RESEARCH_SCHEMA
from backend.utils.json_sanitize import extract_json_text
from backend.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


class ResearchRequest(BaseModel):
    """Input payload for the research step."""

    topic: str
    audience: str
    age: str | None = None
    depth: int = Field(default=1, ge=1, le=5)
    model: str = Field(default=DEFAULT_CHAT_MODEL)
    reasoning_effort: str = Field(default="auto")


class ResearchResponse(BaseModel):
    """Structured response returned to the client."""

    analysis: str
    highlights: list[str]
    segments: list[str]


def _normalise_text(raw_text: str) -> str:
    cleaned = extract_json_text(raw_text or "").replace("\ufeff", "").replace("\x00", "")
    return cleaned.strip()


def _extract_highlights(text: str) -> list[str]:
    highlights: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "•")):
            bullet = stripped.lstrip("-• ").strip()
            if bullet:
                highlights.append(bullet)
            continue
        heading = re.match(r"^([A-Z][A-Z\s]+):\s*(.+)$", stripped)
        if heading:
            remainder = heading.group(2).strip()
            if remainder:
                highlights.append(remainder)
    if not highlights and text:
        sample = text.splitlines()
        if sample:
            highlights.append(sample[0].strip())
    return highlights


def _split_segments(text: str) -> list[str]:
    segments = [segment.strip() for segment in text.split("\n\n") if segment.strip()]
    if not segments and text:
        segments = [text]
    return segments


@retry_with_exponential_backoff()
def _create_research_completion(
    client: Any,
    messages: list[dict[str, str]],
    model: str,
    effort: str,
) -> str:
    """Invoke the appropriate OpenAI API and return the text response."""
    if is_reasoning_model(model):
        response = client.responses.create(
            model=model,
            input=messages,
            reasoning={"effort": effort},
            temperature=0.4,
        )
        return getattr(response, "output_text", "")
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4,
        )
        return getattr(response.choices[0].message, "content", "") if response.choices else ""


def _render_research_messages(req: ResearchRequest) -> list[dict[str, str]]:
    audience_age = req.age or "all ages"
    user_prompt = (
        RESEARCH_USER.replace("$topic", req.topic)
        .replace("$audience", req.audience)
        .replace("$age", audience_age)
        .replace("$depth", str(req.depth))
    )
    return [
        {"role": "system", "content": RESEARCH_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]


@router.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest) -> ResearchResponse:
    """Generate textual design research for the requested topic."""
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

    messages = _render_research_messages(req)

    try:
        raw_text = _create_research_completion(
            client,
            messages,
            model=req.model,
            effort=req.reasoning_effort,
        )
    except Exception as exc:  # pragma: no cover - retried failure
        logger.error("OpenAI research completion failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM API call failed",
        )

    cleaned = _normalise_text(raw_text)
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Empty output from model",
        )

    payload = ResearchResponse(
        analysis=cleaned,
        highlights=_extract_highlights(cleaned),
        segments=_split_segments(cleaned),
    )

    # Validate shape with the lightweight schema for consistency.
    if RESEARCH_SCHEMA is not None:
        try:
            from jsonschema import validate as jsonschema_validate  # local import to avoid cost if unused

            jsonschema_validate(instance=payload.model_dump(), schema=RESEARCH_SCHEMA)
        except Exception:  # pragma: no cover - schema is advisory only
            logger.info("Research payload deviated from advisory schema; continuing.")

    return payload


__all__ = ["router", "ResearchRequest", "ResearchResponse", "research"]
