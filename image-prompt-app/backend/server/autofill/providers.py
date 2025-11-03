"""Providers that execute research requests via the OpenAI Responses API."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from .models import AUTOFILL_JSON_SCHEMA

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("RESEARCH_MODEL", "gpt-4.1-nano")
DEFAULT_TIMEOUT = float(os.getenv("RESEARCH_TIMEOUT_S", "45"))
DEFAULT_PROVIDER = os.getenv("RESEARCH_PROVIDER", "openai_web")


class ResearchProviderError(RuntimeError):
    """Raised when the remote research provider fails."""


class WebToolUnavailableError(ResearchProviderError):
    """Raised when the web tool is not accessible for the current key."""


@dataclass
class ProviderResult:
    payload: Dict[str, Any]
    used_web: bool


class OpenAIResponsesProvider:
    """Call the OpenAI Responses API with strict JSON schema enforcement."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout_s: float = DEFAULT_TIMEOUT,
        provider_mode: str = DEFAULT_PROVIDER,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.timeout_s = timeout_s
        self.provider_mode = provider_mode
        if not self.api_key:
            raise ResearchProviderError("OPENAI_API_KEY is required for research")

    @property
    def allow_web(self) -> bool:
        return self.provider_mode == "openai_web"

    def _build_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        use_web: bool,
    ) -> Dict[str, Any]:
        tools = [{"type": "web_search"}] if use_web else []
        payload: Dict[str, Any] = {
            "model": self.model,
            "modalities": ["text"],
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "text": {
                "format": "json_schema",
                "json_schema": {
                    "name": "autofill_schema",
                    "strict": True,
                    "schema": AUTOFILL_JSON_SCHEMA,
                },
            },
            "temperature": 0.3,
            "max_output_tokens": 1600,
        }
        if tools:
            payload["tools"] = tools
        return payload

    def _parse_json(self, value: str) -> Dict[str, Any]:
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ResearchProviderError("Failed to decode JSON payload") from exc

    def _extract_json(self, response_payload: Dict[str, Any]) -> Dict[str, Any]:
        if "output" in response_payload:
            for block in response_payload["output"]:
                if block.get("type") != "message":
                    continue
                content = block.get("content", [])
                for item in content:
                    text = item.get("text") or item.get("value")
                    if text:
                        return self._parse_json(text)
        if "output_text" in response_payload:
            return self._parse_json(response_payload["output_text"])
        if "data" in response_payload:
            return self._parse_json(response_payload["data"][0]["content"][0]["text"])
        raise ResearchProviderError("Unable to extract JSON payload from response")

    def research(
        self,
        system_prompt: str,
        user_prompt: str,
        use_web: bool,
        max_attempts: int = 3,
    ) -> ProviderResult:
        attempts = max(1, max_attempts)
        last_error: Optional[Exception] = None
        for attempt in range(attempts):
            payload = self._build_payload(system_prompt, user_prompt, use_web)
            try:
                LOGGER.debug("Calling OpenAI Responses API (attempt %s, web=%s)", attempt + 1, use_web)
                response = httpx.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.timeout_s,
                )
                response.raise_for_status()
                data = response.json()
                parsed = self._extract_json(data)
                return ProviderResult(payload=parsed, used_web=bool(payload["tools"]))
            except httpx.HTTPStatusError as exc:  # type: ignore[unreachable]
                last_error = exc
                message = exc.response.text
                LOGGER.error("OpenAI Responses API returned %s: %s", exc.response.status_code, message)
                if use_web and exc.response.status_code in {400, 404, 422}:
                    detail = (message or "").lower()
                    if "tool" in detail or "web" in detail:
                        raise WebToolUnavailableError("OpenAI web tool unavailable") from exc
                if exc.response.status_code in {401, 403}:
                    raise ResearchProviderError("Unauthorized OpenAI request") from exc
            except (json.JSONDecodeError, ResearchProviderError) as exc:
                last_error = exc
                LOGGER.warning("Failed to parse JSON output: %s", exc)
            except httpx.HTTPError as exc:
                last_error = exc
                LOGGER.error("HTTP error while calling OpenAI Responses API: %s", exc)
                break
        raise ResearchProviderError(str(last_error) if last_error else "OpenAI research failed")
