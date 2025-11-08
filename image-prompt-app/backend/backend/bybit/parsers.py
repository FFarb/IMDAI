"""Helpers for normalising Bybit instrument payloads."""
from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert a Bybit numeric string to float, returning ``default`` on failure."""

    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            logger.debug("Unable to parse float from value %s", value)
            return default
    return default


def to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Convert a Bybit numeric string to int, returning ``default`` on failure."""

    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            logger.debug("Unable to parse int from value %s", value)
            return default
    return default


def pick(payload: Mapping[str, Any], *path: str) -> Any:
    """Safely walk nested mappings using ``path`` keys."""

    current: Any = payload
    for key in path:
        if isinstance(current, Mapping) and key in current:
            current = current[key]
        else:
            return None
    return current


def get_contract_size(payload: Mapping[str, Any], category: str) -> float:
    """Resolve contract size for an instrument regardless of schema revision."""

    for candidate in ("contractSize", "contractVal"):
        if candidate in payload and payload[candidate] is not None:
            value = to_float(payload[candidate])
            if value:
                return value

    logger.warning(
        "Bybit instrument missing contract size field; defaulting to 1.0 for %s", payload.get("symbol")
    )
    if category.lower() == "linear":
        return 1.0
    return 1.0


__all__ = [
    "get_contract_size",
    "pick",
    "to_float",
    "to_int",
]
