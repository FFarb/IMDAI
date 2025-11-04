from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from openai_client import GPT_SYNTH_MODEL, get_openai_client, has_valid_key
from prompts import SYNTH_SYSTEM, SYNTH_USER
from schemas import SYNTHESIS_SCHEMA
from utils.json_sanitize import parse_model_json
from utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pipeline"])


# ----- Pydantic Models ---------------------------------------------------------

# The request model expects the full research output from the previous step
class SynthesisRequest(BaseModel):
    research: dict[str, Any]
    audience: str
    age: str
    variants: int = Field(default=2, ge=1, le=5)

# Pydantic model for the expected Synthesis output structure
class SynthesisOutput(BaseModel):
    prompts: list

# ----- Helper Function ---------------------------------------------------------

@retry_with_exponential_backoff(tries=3)
def _call_synthesis_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Invoke the OpenAI API for the synthesis step."""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    payload = {
        "model": GPT_SYNTH_MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.8, # Higher temp for more creative variation
    }

    try:
        response = client.chat.completions.create(**payload)
        raw_text = response.choices[0].message.content or ""
        if not raw_text.strip():
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Empty output from model")

        json_data = parse_model_json(raw_text)
        return json_data

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"LLM call failed after retries: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LLM API call failed: {exc}")


# ----- Route -------------------------------------------------------------------

@router.post("/synthesize", response_model=SynthesisOutput)
def synthesize(req: SynthesisRequest) -> dict[str, Any]:
    """
    Takes research data and generates a set of creative prompts for image generation.
    """
    if not has_valid_key():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPENAI_API_KEY not configured")

    # Simple template rendering
    system_prompt = SYNTH_SYSTEM.replace("$max_variants", str(req.variants))
    user_prompt = SYNTH_USER.replace("$RESEARCH_JSON", json.dumps(req.research, ensure_ascii=False))\
                            .replace("$audience", req.audience)\
                            .replace("$age", req.age)\
                            .replace("$variants", str(req.variants))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    llm_result = _call_synthesis_llm(messages)

    try:
        validated_data = SynthesisOutput.model_validate(llm_result)
        return validated_data.model_dump()
    except ValidationError as exc:
        logger.error(f"LLM output failed validation for /synthesize: {exc}\nRaw data: {llm_result}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The model's output did not match the required schema: {exc}",
        )
