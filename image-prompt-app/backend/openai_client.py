"""Utilities for managing a shared OpenAI client instance and environment variables."""
from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()

# --- Environment Variable Loading ---

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY or "your-api" in _OPENAI_API_KEY.lower():
    logger.warning("OPENAI_API_KEY not set or is a placeholder. OpenAI calls will fail.")

# Model configuration with fallbacks
GPT_RESEARCH_MODEL = os.getenv("GPT_RESEARCH_MODEL", "gpt-4o-mini")
GPT_SYNTH_MODEL = os.getenv("GPT_SYNTH_MODEL", "gpt-4-nano")
GPT_IMAGE_MODEL = os.getenv("GPT_IMAGE_MODEL", "dall-e-3") # Assuming gpt-image-1 was a placeholder

# Gradient policy flag
_allow_true_gradients_str = os.getenv("ALLOW_TRUE_GRADIENTS", "false").lower()
ALLOW_TRUE_GRADIENTS = _allow_true_gradients_str in ("true", "1", "yes", "on")

logger.info(f"Research Model: {GPT_RESEARCH_MODEL}")
logger.info(f"Synthesis Model: {GPT_SYNTH_MODEL}")
logger.info(f"Image Model: {GPT_IMAGE_MODEL}")
logger.info(f"Allow True Gradients: {ALLOW_TRUE_GRADIENTS}")


# --- OpenAI Client Initialization ---

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
