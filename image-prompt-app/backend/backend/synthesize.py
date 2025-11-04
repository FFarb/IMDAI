"""Synthesis stage endpoint for converting research into prompts."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from jsonschema import ValidationError as SchemaValidationError, validate as jsonschema_validate

from backend.openai_client import GPT_SYNTH_MODEL, get_openai_client, has_valid_key
from backend.prompts import SYNTH_SYSTEM, SYNTH_USER
from backend.schemas import SYNTHESIS_SCHEMA
from backend.utils.json_sanitize import parse_model_json
from backend.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


class SynthesisRequest(BaseModel):
    """Input payload for the synthesis step."""

    research: dict[str, Any]
    audience: str
    age: str | None = None
    variants: int = Field(default=1, ge=1, le=6)


@retry_with_exponential_backoff()
def _create_synthesis_completion(client: Any, messages: list[dict[str, str]]) -> Any:
    """Invoke the OpenAI API and return the raw completion object."""

    return client.chat.completions.create(
        model=GPT_SYNTH_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.8,
    )


def _render_synthesis_messages(req: SynthesisRequest) -> list[dict[str, str]]:
    research_json = json.dumps(req.research, ensure_ascii=False)
    audience_age = req.age or "all ages"
    system_prompt = SYNTH_SYSTEM.replace("$max_variants", str(req.variants))
    user_prompt = (
        SYNTH_USER.replace("$RESEARCH_JSON", research_json)
        .replace("$audience", req.audience)
        .replace("$age", audience_age)
        .replace("$variants", str(req.variants))
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


@router.post("/synthesize")
def synthesize(req: SynthesisRequest) -> dict[str, Any]:
    """Generate structured image prompts from research insights."""

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
    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Empty output from model",
        )

    try:
        parsed = parse_model_json(raw_text)
    except ValueError as exc:
        logger.error("Failed to parse synthesis JSON: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid JSON from model",
        )

    try:
        jsonschema_validate(instance=parsed, schema=SYNTHESIS_SCHEMA)
    except SchemaValidationError as exc:
        logger.error("Synthesis JSON failed schema validation: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model output did not match SYNTHESIS_SCHEMA",
        )

    return parsed


__all__ = ["router", "SynthesisRequest", "synthesize"]
