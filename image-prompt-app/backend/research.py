from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from openai_client import GPT_RESEARCH_MODEL, get_openai_client, has_valid_key
from prompts import RESEARCH_SYSTEM, RESEARCH_USER
from schemas import RESEARCH_SCHEMA
from utils.json_sanitize import parse_model_json
from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


# ----- Pydantic Models ---------------------------------------------------------

class ResearchRequest(BaseModel):
    topic: str
    audience: str
    age: str
    depth: int = Field(default=3, ge=1, le=5)

# Pydantic model for the expected Research output structure for validation
class ResearchOutput(BaseModel):
    references: list
    designs: list
    palette: list | None = None
    notes: str | None = None
    color_distribution: list
    light_distribution: dict
    gradient_distribution: list

# ----- Helper Function ---------------------------------------------------------

@retry_with_exponential_backoff(tries=3)
def _call_research_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Invoke the OpenAI API and handle response parsing and validation."""
    client = get_openai_client()
    # The guard is now inside the retry loop
    if not client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    payload = {
        "model": GPT_RESEARCH_MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.5,
    }

    try:
        response = client.chat.completions.create(**payload)
        raw_text = response.choices[0].message.content or ""
        if not raw_text.strip():
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Empty output from model")

        json_data = parse_model_json(raw_text)
        return json_data

    except HTTPException:
        raise  # Re-raise known HTTP exceptions
    except Exception as exc:
        logger.error(f"LLM call failed after retries: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LLM API call failed: {exc}")


# ----- Route -------------------------------------------------------------------

@router.post("/research", response_model=ResearchOutput)
def research(req: ResearchRequest) -> dict[str, Any]:
    """
    Given a topic, audience, and age, performs web research to generate design
    ideas, color palettes, and distribution analyses.
    """
    if not has_valid_key():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    # Simple template rendering
    user_prompt = RESEARCH_USER.replace("$topic", req.topic)\
                               .replace("$audience", req.audience)\
                               .replace("$age", req.age)\
                               .replace("$depth", str(req.depth))

    messages = [
        {"role": "system", "content": RESEARCH_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    llm_result = _call_research_llm(messages)

    try:
        # Validate the structure of the LLM's JSON output
        validated_data = ResearchOutput.model_validate(llm_result)
        return validated_data.model_dump()
    except ValidationError as exc:
        logger.error(f"LLM output failed validation for /research: {exc}\nRaw data: {llm_result}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The model's output did not match the required schema: {exc}",
        )
