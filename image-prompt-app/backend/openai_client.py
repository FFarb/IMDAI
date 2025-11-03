"""Utilities for managing a shared OpenAI client instance."""
from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY or "your-api" in _OPENAI_API_KEY.lower():
    logger.error("OPENAI_API_KEY not set or invalid. Requests will fail until configured.")

_client: Optional[OpenAI] = None
if _OPENAI_API_KEY and "your-api" not in _OPENAI_API_KEY.lower():
    try:
        _client = OpenAI(api_key=_OPENAI_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error("Failed to initialize OpenAI client: %s", exc)
        _client = None


def get_openai_client() -> Optional[OpenAI]:
    """Return the shared OpenAI client instance if configured."""
    return _client


def has_valid_key() -> bool:
    """Return True when a non-placeholder API key is available."""
    return _client is not None
