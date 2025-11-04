"""Utilities for managing the shared OpenAI client and runtime feature flags."""
from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

GPT_RESEARCH_MODEL = "gpt-4o-mini-2024-07-18"
GPT_SYNTH_MODEL = "gpt-4o-mini-2024-07-18"
GPT_IMAGE_MODEL = "gpt-image-1"

ALLOW_TRUE_GRADIENTS = os.getenv("ALLOW_TRUE_GRADIENTS", "false").lower() in {
    "1",
    "true",
    "yes",
}

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _is_placeholder_key(key: str | None) -> bool:
    """Return ``True`` when the provided key should not be used."""
    if not key:
        return True
    candidate = key.strip().lower()
    return candidate in {"sk-xxxx"} or "your-api" in candidate


_client: Optional[OpenAI]
if _is_placeholder_key(_OPENAI_API_KEY):
    _client = None
    if _OPENAI_API_KEY:
        logger.warning("Ignoring placeholder OPENAI_API_KEY value.")
else:
    try:
        _client = OpenAI(api_key=_OPENAI_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning("Failed to initialise OpenAI client: %s", exc)
        _client = None


def get_openai_client() -> Optional[OpenAI]:
    """Return the configured :class:`~openai.OpenAI` client, if any."""
    return _client


def has_valid_key() -> bool:
    """Return ``True`` when a usable OpenAI API key is configured."""
    return _client is not None


__all__ = [
    "ALLOW_TRUE_GRADIENTS",
    "GPT_IMAGE_MODEL",
    "GPT_RESEARCH_MODEL",
    "GPT_SYNTH_MODEL",
    "get_openai_client",
    "has_valid_key",
]
