"""Research stage endpoint for the three-stage design pipeline."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from jsonschema import ValidationError as SchemaValidationError, validate as jsonschema_validate

from backend.openai_client import GPT_RESEARCH_MODEL, get_openai_client, has_valid_key
from backend.prompts import RESEARCH_SYSTEM, RESEARCH_USER
from backend.schemas import RESEARCH_SCHEMA
from backend.utils.json_sanitize import parse_model_json
from backend.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


class ResearchRequest(BaseModel):
    """Input payload for the research step."""

    topic: str
    audience: str
    age: str | None = None
    depth: int = Field(default=1, ge=1, le=5)


@retry_with_exponential_backoff()
def _create_research_completion(client: Any, messages: list[dict[str, str]]) -> Any:
    """Invoke the OpenAI API and return the raw completion object."""

    return client.chat.completions.create(
        model=GPT_RESEARCH_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.5,
    )


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


@router.post("/research")
def research(req: ResearchRequest) -> dict[str, Any]:
    """Generate structured design research for the requested topic."""

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
        response = _create_research_completion(client, messages)
    except Exception as exc:  # pragma: no cover - retried failure
        logger.error("OpenAI research completion failed: %s", exc, exc_info=True)
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
        logger.error("Failed to parse research JSON: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid JSON from model",
        )

    try:
        jsonschema_validate(instance=parsed, schema=RESEARCH_SCHEMA)
    except SchemaValidationError as exc:
        logger.error("Research JSON failed schema validation: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model output did not match RESEARCH_SCHEMA",
        )

    return parsed


__all__ = ["router", "ResearchRequest", "research"]
