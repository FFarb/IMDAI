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
from backend.prompts import (
    RESEARCH_SYSTEM_PROMPT_DEEP_EXECUTE,
    RESEARCH_SYSTEM_PROMPT_DEEP_PLAN,
    RESEARCH_SYSTEM_PROMPT_EXPERT_EXECUTE,
    RESEARCH_SYSTEM_PROMPT_EXPERT_JUDGE,
    RESEARCH_SYSTEM_PROMPT_EXPERT_PLAN,
    RESEARCH_SYSTEM_PROMPT_QUICK,
    RESEARCH_USER_PROMPT_DEEP_EXECUTE,
    RESEARCH_USER_PROMPT_DEEP_PLAN,
    RESEARCH_USER_PROMPT_EXPERT_EXECUTE,
    RESEARCH_USER_PROMPT_EXPERT_JUDGE,
    RESEARCH_USER_PROMPT_EXPERT_PLAN,
    RESEARCH_USER_PROMPT_QUICK,
)
from backend.schemas import RESEARCH_SCHEMA
from backend.utils.json_sanitize import extract_json_text, parse_model_json
from backend.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


class ResearchRequest(BaseModel):
    """Input payload for the research step."""

    topic: str
    audience: str
    age: str | None = None
    research_mode: str = Field(default="quick")
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
def _call_llm_api(
    client: Any,
    messages: list[dict[str, str]],
    model: str,
    effort: str,
    json_mode: bool = False,
) -> str:
    """Invoke the appropriate OpenAI API and return the text response."""
    kwargs = {"model": model, "messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    if is_reasoning_model(model):
        response = client.responses.create(input=messages, reasoning={"effort": effort}, **kwargs)
        return getattr(response, "output_text", "")
    else:
        response = client.chat.completions.create(**kwargs)
        return getattr(response.choices[0].message, "content", "") if response.choices else ""


def _render_research_messages(
    system_prompt: str,
    user_prompt_template: str,
    req: ResearchRequest,
    **kwargs: str,
) -> list[dict[str, str]]:
    """Render the chat messages for the research LLM call."""
    audience_age = req.age or "all ages"
    user_prompt = (
        user_prompt_template.replace("$topic", req.topic)
        .replace("$audience", req.audience)
        .replace("$age", audience_age)
    )
    for key, value in kwargs.items():
        user_prompt = user_prompt.replace(f"${key}", value)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _run_quick_research(client: Any, req: ResearchRequest) -> str:
    """Run the quick research mode."""
    messages = _render_research_messages(
        RESEARCH_SYSTEM_PROMPT_QUICK,
        RESEARCH_USER_PROMPT_QUICK,
        req,
    )
    return _call_llm_api(
        client,
        messages,
        model=req.model,
        effort=req.reasoning_effort,
        json_mode=True,
    )


def _run_deep_research(client: Any, req: ResearchRequest) -> str:
    """Run the deep research mode using a plan-and-execute strategy."""
    # Plan step
    plan_messages = _render_research_messages(
        RESEARCH_SYSTEM_PROMPT_DEEP_PLAN,
        RESEARCH_USER_PROMPT_DEEP_PLAN,
        req,
    )
    plan_text = _call_llm_api(
        client,
        plan_messages,
        model=req.model,
        effort=req.reasoning_effort,
        json_mode=True,
    )
    plan = parse_model_json(plan_text).get("research_plan", [])

    # Execute step
    execute_messages = _render_research_messages(
        RESEARCH_SYSTEM_PROMPT_DEEP_EXECUTE,
        RESEARCH_USER_PROMPT_DEEP_EXECUTE,
        req,
        research_plan=str(plan),
    )
    return _call_llm_api(
        client,
        execute_messages,
        model=req.model,
        effort=req.reasoning_effort,
        json_mode=True,
    )


def _run_expert_research(client: Any, req: ResearchRequest) -> str:
    """Run the expert research mode using a plan-and-execute strategy with a judge."""
    # Plan step
    plan_messages = _render_research_messages(
        RESEARCH_SYSTEM_PROMPT_EXPERT_PLAN,
        RESEARCH_USER_PROMPT_EXPERT_PLAN,
        req,
    )
    plan_text = _call_llm_api(
        client,
        plan_messages,
        model=req.model,
        effort=req.reasoning_effort,
        json_mode=True,
    )
    plan = parse_model_json(plan_text).get("research_plan", [])

    # Execute step
    execute_messages = _render_research_messages(
        RESEARCH_SYSTEM_PROMPT_EXPERT_EXECUTE,
        RESEARCH_USER_PROMPT_EXPERT_EXECUTE,
        req,
        research_plan=str(plan),
    )
    draft_research = _call_llm_api(
        client,
        execute_messages,
        model=req.model,
        effort=req.reasoning_effort,
        json_mode=True,
    )

    # Judge step
    judge_messages = _render_research_messages(
        RESEARCH_SYSTEM_PROMPT_EXPERT_JUDGE,
        RESEARCH_USER_PROMPT_EXPERT_JUDGE,
        req,
        research_plan=str(plan),
        draft_research=draft_research,
    )
    return _call_llm_api(
        client,
        judge_messages,
        model=req.model,
        effort=req.reasoning_effort,
        json_mode=True,
    )


@router.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest) -> ResearchResponse:
    """Generate textual design research for the requested topic."""
    if not has_valid_key():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )

    client = get_openai_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY not configured",
        )

    try:
        if req.research_mode == "quick":
            raw_text = _run_quick_research(client, req)
        elif req.research_mode == "deep":
            raw_text = _run_deep_research(client, req)
        elif req.research_mode == "expert":
            raw_text = _run_expert_research(client, req)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid research mode: {req.research_mode}",
            )
    except Exception as exc:
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
