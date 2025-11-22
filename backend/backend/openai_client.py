"""Utilities for managing the shared OpenAI client and runtime feature flags."""
from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_CHAT_MODEL = "gpt-4o-mini-2024-07-18"
GPT_SYNTH_MODEL = "gpt-4o-mini-2024-07-18"
DEFAULT_IMAGE_MODEL = "dall-e-3"

# Models that use the new Reasoning API
REASONING_MODELS = {"gpt-5-large", "gpt-5-small"}

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


def is_reasoning_model(model_name: str) -> bool:
    """Return ``True`` if the model uses the new Reasoning API."""
    return model_name.lower() in REASONING_MODELS


def get_model(model_name: str = DEFAULT_CHAT_MODEL, temperature: float = 0.7) -> ChatOpenAI:
    """Create and return a ChatOpenAI model instance.
    
    Args:
        model_name: The OpenAI model to use (default: gpt-4o-mini-2024-07-18).
        temperature: Temperature setting for the model (default: 0.7).
        
    Returns:
        ChatOpenAI instance configured with the specified parameters.
        
    Raises:
        ValueError: If no valid OpenAI API key is configured.
    """
    if not has_valid_key():
        raise ValueError(
            "No valid OpenAI API key configured. "
            "Please set OPENAI_API_KEY in your .env file."
        )
    
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=_OPENAI_API_KEY,
    )


__all__ = [
    "ALLOW_TRUE_GRADIENTS",
    "DEFAULT_IMAGE_MODEL",
    "DEFAULT_CHAT_MODEL",
    "GPT_SYNTH_MODEL",
    "get_openai_client",
    "has_valid_key",
    "is_reasoning_model",
    "get_model",
]
