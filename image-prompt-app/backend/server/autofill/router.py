"""FastAPI router exposing autofill research endpoints."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool

from .models import AutofillResponse, ResearchFlags, ResearchRequest
from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from .providers import OpenAIResponsesProvider, ResearchProviderError, WebToolUnavailableError
from .validators import AutofillValidationError, validate_autofill_payload, validate_master_prompt

LOGGER = logging.getLogger(__name__)

MAX_SOURCES = int(os.getenv("RESEARCH_MAX_SOURCES", "8"))
DEFAULT_AVOID_BRANDS = os.getenv("RESEARCH_AVOID_BRANDS", "true").lower() == "true"
DEFAULT_KIDS_SAFE = os.getenv("RESEARCH_KIDS_SAFE", "true").lower() == "true"

router = APIRouter(prefix="/autofill", tags=["autofill"])


_provider: OpenAIResponsesProvider | None = None


def get_provider() -> OpenAIResponsesProvider:
    global _provider
    if _provider is None:
        _provider = OpenAIResponsesProvider()
    return _provider


def reset_provider(provider: OpenAIResponsesProvider | None) -> None:
    global _provider
    _provider = provider


async def _dispatch_image_generation(request: Request, payload: Dict[str, Any]) -> Any:
    async with httpx.AsyncClient(app=request.app, base_url="http://testserver") as client:
        response = await client.post("/api/image", json=payload)
        response.raise_for_status()
        return response.json()


def _compose_user_prompt(req: ResearchRequest) -> str:
    return USER_PROMPT_TEMPLATE.format(topic=req.topic, audience=req.audience, age=req.age)


async def _execute_research(
    req: ResearchRequest,
    provider: OpenAIResponsesProvider,
    response: Response,
) -> AutofillResponse:
    flags = ResearchFlags(**req.flags.model_dump())
    if DEFAULT_AVOID_BRANDS:
        flags.avoid_brands = True
    if DEFAULT_KIDS_SAFE:
        flags.kids_safe = True
    use_web = flags.use_web and provider.allow_web
    try:
        result = await run_in_threadpool(
            provider.research,
            SYSTEM_PROMPT,
            _compose_user_prompt(req),
            use_web,
        )
    except WebToolUnavailableError:
        if not use_web:
            raise HTTPException(status_code=503, detail="OpenAI web tool unavailable")
        LOGGER.warning("Web tool unavailable, retrying without web search")
        response.headers["X-Autofill-Warning"] = "openai_web_unavailable"
        result = await run_in_threadpool(
            provider.research,
            SYSTEM_PROMPT,
            _compose_user_prompt(req),
            False,
        )
    except ResearchProviderError as exc:
        LOGGER.error("Failed to perform research: %s", exc)
        raise HTTPException(status_code=502, detail="Research provider failed") from exc

    try:
        traits = validate_autofill_payload(result.payload, flags, MAX_SOURCES)
        master_prompt_text = validate_master_prompt(traits, result.payload, flags)
    except AutofillValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    autofill_response = AutofillResponse(
        traits=traits,
        master_prompt_text=master_prompt_text,
        master_prompt_json=result.payload.get("master_prompt_json", {}),
    )
    return autofill_response


@router.post("/research", response_model=AutofillResponse)
async def research(
    req: ResearchRequest,
    response: Response,
    provider: OpenAIResponsesProvider = Depends(get_provider),
) -> AutofillResponse:
    return await _execute_research(req, provider, response)


@router.post("/one_click_generate")
async def one_click_generate(
    req: ResearchRequest,
    response: Response,
    request: Request,
    provider: OpenAIResponsesProvider = Depends(get_provider),
) -> Dict[str, Any]:
    autofill_response = await _execute_research(req, provider, response)
    payload = {
        "prompt": {
            "positive": autofill_response.master_prompt_text,
            "negative": ", ".join(autofill_response.traits.negative),
            "params": {},
        },
        "n": req.images_n,
    }
    try:
        images = await _dispatch_image_generation(request, payload)
    except httpx.HTTPStatusError as exc:
        LOGGER.error("Image generation failed: %s", exc)
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        LOGGER.error("HTTP error when generating images: %s", exc)
        raise HTTPException(status_code=502, detail="Image generation failed") from exc
    return {"autofill": autofill_response, "images": images}
