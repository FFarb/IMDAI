"""Validation and sanitation helpers for autofill research results."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence

from pydantic import ValidationError

from .models import DatasetTraits, PaletteColor, ResearchFlags, SourceLink

COMPOSITION_WHITELIST = {"centered", "single character", "subtle lattice", "grid", "minimal frame"}
MANDATORY_NEGATIVE = [
    "photo-realism",
    "photographic textures",
    "noise",
    "background patterns",
    "brand logos",
    "trademark words",
]
PRINT_READY_CONSTANTS = [
    "transparent background",
    "no shadows",
    "no gradients",
    "no textures",
    "clean vector edges",
    "centered standalone composition",
]
BRAND_TERMS = {
    "adidas",
    "apple",
    "barbie",
    "coca-cola",
    "disney",
    "google",
    "lego",
    "marvel",
    "mcdonalds",
    "nike",
    "pepsi",
    "pixar",
    "pokemon",
    "starbucks",
}
KIDS_UNSAFE_TERMS = {
    "blood",
    "gore",
    "gun",
    "weapon",
    "alcohol",
    "cigarette",
    "cigar",
    "violence",
    "nudity",
    "sex",
}

BRAND_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(term) for term in sorted(BRAND_TERMS)) + r")\b", re.IGNORECASE)
KIDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(term) for term in sorted(KIDS_UNSAFE_TERMS)) + r")\b", re.IGNORECASE)
HEX_PATTERN = re.compile(r"^#([A-Fa-f0-9]{6})$")


class AutofillValidationError(ValueError):
    """Raised when the LLM response violates guardrails."""


def _normalize_hex(hex_value: str) -> str:
    match = HEX_PATTERN.fullmatch(hex_value.strip())
    if not match:
        raise AutofillValidationError(f"Invalid HEX value: {hex_value}")
    return f"#{match.group(1).upper()}"


def _normalize_palette(raw_palette: Sequence[Dict[str, Any]]) -> List[PaletteColor]:
    seen: Dict[str, float] = {}
    for color in raw_palette:
        hex_value = _normalize_hex(str(color.get("hex")))
        weight = float(color.get("weight", 0))
        if weight < 0:
            raise AutofillValidationError(f"Negative palette weight: {weight}")
        seen[hex_value] = seen.get(hex_value, 0.0) + weight
    if not (5 <= len(seen) <= 7):
        raise AutofillValidationError("Palette must contain 5–7 unique colors")
    total_weight = sum(seen.values())
    if total_weight <= 0:
        equal_weight = round(1 / len(seen), 4)
        normalized = [PaletteColor(hex=hex_value, weight=equal_weight) for hex_value in seen]
    else:
        normalized = [PaletteColor(hex=hex_value, weight=value / total_weight) for hex_value, value in seen.items()]
    normalization_sum = sum(color.weight for color in normalized)
    for color in normalized:
        color.weight = round(color.weight / normalization_sum, 4)
    return normalized


def _sanitize_list(values: Iterable[str]) -> List[str]:
    sanitized = []
    for value in values:
        normalized = value.strip().lower()
        if not normalized:
            continue
        sanitized.append(normalized)
    return sanitized


def _filter_brands(values: Iterable[str]) -> List[str]:
    filtered = []
    for value in values:
        if BRAND_PATTERN.search(value):
            continue
        filtered.append(value)
    return filtered


def _ensure_kids_safe(values: Iterable[str]) -> None:
    for value in values:
        if KIDS_PATTERN.search(value):
            raise AutofillValidationError(f"Kids-unsafe term detected: {value}")


def _ensure_no_brand_text(value: str) -> None:
    if BRAND_PATTERN.search(value):
        raise AutofillValidationError("Brand or trademark detected in master prompt")


def _sanitize_typography(values: Iterable[str], avoid_brands: bool) -> List[str]:
    sanitized = _sanitize_list(values)
    if avoid_brands:
        sanitized = _filter_brands(sanitized)
    if len(sanitized) > 3:
        sanitized = sanitized[:3]
    return sanitized


def _sanitize_motifs(values: Iterable[str], avoid_brands: bool, kids_safe: bool) -> List[str]:
    sanitized = _sanitize_list(values)
    if avoid_brands:
        sanitized = _filter_brands(sanitized)
    if kids_safe:
        _ensure_kids_safe(sanitized)
    unique_ordered: List[str] = []
    for item in sanitized:
        if item not in unique_ordered:
            unique_ordered.append(item)
    if not (8 <= len(unique_ordered) <= 12):
        raise AutofillValidationError("Motifs must contain 8–12 safe generic tags")
    return unique_ordered


def _sanitize_sources(values: Any, max_sources: int) -> List[SourceLink]:
    if values in (None, []):
        return []
    if not isinstance(values, list):
        raise AutofillValidationError("Sources must be a list of {title,url}")
    sanitized: List[SourceLink] = []
    for entry in values[:max_sources]:
        try:
            sanitized.append(SourceLink(**entry))
        except ValidationError as exc:
            raise AutofillValidationError(f"Invalid source entry: {entry}") from exc
    return sanitized


def validate_autofill_payload(
    payload: Dict[str, Any],
    flags: ResearchFlags,
    max_sources: int,
) -> DatasetTraits:
    palette = _normalize_palette(payload.get("palette", []))
    motifs = _sanitize_motifs(payload.get("motifs", []), flags.avoid_brands, flags.kids_safe)
    typography = _sanitize_typography(payload.get("typography", []), flags.avoid_brands)
    composition = [value.strip().lower() for value in payload.get("composition", []) if value]
    unique_composition: List[str] = []
    for value in composition:
        if value not in unique_composition:
            unique_composition.append(value)
    if any(item not in COMPOSITION_WHITELIST for item in unique_composition):
        raise AutofillValidationError("Composition contains items outside whitelist")
    mood = _sanitize_list(payload.get("mood", []))[:3]
    if flags.kids_safe:
        _ensure_kids_safe(mood)
    seed_examples = payload.get("seed_examples", [])
    if not (2 <= len(seed_examples) <= 3):
        raise AutofillValidationError("Seed examples must contain 2–3 items")
    if flags.avoid_brands and any(BRAND_PATTERN.search(example) for example in seed_examples):
        raise AutofillValidationError("Seed examples contain brand terms")
    negative = payload.get("negative") or []
    negative = [item.strip().lower() for item in negative if item]
    for term in MANDATORY_NEGATIVE:
        if term not in negative:
            negative.append(term)
    sources = _sanitize_sources(payload.get("sources"), max_sources)
    traits_payload = {
        "palette": [color.model_dump() for color in palette],
        "motifs": motifs,
        "line_weight": payload.get("line_weight"),
        "outline": payload.get("outline"),
        "typography": typography,
        "composition": unique_composition or ["centered"],
        "audience": payload.get("audience", ""),
        "age": payload.get("age", ""),
        "mood": mood,
        "negative": negative,
        "seed_examples": seed_examples,
        "sources": [source.model_dump() for source in sources] or None,
    }
    try:
        traits = DatasetTraits(**traits_payload)
    except ValidationError as exc:
        raise AutofillValidationError("Dataset traits validation failed") from exc
    return traits


def _check_json_for_brands(data: Any) -> None:
    if isinstance(data, str):
        if BRAND_PATTERN.search(data):
            raise AutofillValidationError("master_prompt_json contains brand terms")
    elif isinstance(data, list):
        for item in data:
            _check_json_for_brands(item)
    elif isinstance(data, dict):
        for value in data.values():
            _check_json_for_brands(value)


def validate_master_prompt(traits: DatasetTraits, payload: Dict[str, Any], flags: ResearchFlags) -> str:
    text = payload.get("master_prompt_text")
    if not isinstance(text, str) or not text.strip():
        raise AutofillValidationError("master_prompt_text must be a non-empty string")
    lower_text = text.lower()
    for constant in PRINT_READY_CONSTANTS:
        if constant not in lower_text:
            raise AutofillValidationError(f"Master prompt missing required phrase: {constant}")
    if flags.avoid_brands:
        _ensure_no_brand_text(lower_text)
    if payload.get("master_prompt_json") is None or not isinstance(payload["master_prompt_json"], dict):
        raise AutofillValidationError("master_prompt_json must be an object")
    json_payload = payload["master_prompt_json"]
    if isinstance(payload.get("audience"), str) and payload["audience"].strip().lower() != traits.audience.lower():
        raise AutofillValidationError("Master prompt audience mismatch")
    if isinstance(payload.get("age"), str) and payload["age"].strip().lower() != traits.age.lower():
        raise AutofillValidationError("Master prompt age mismatch")
    negative = json_payload.get("negative") or []
    for term in MANDATORY_NEGATIVE:
        if term not in [item.lower() for item in negative]:
            raise AutofillValidationError("master_prompt_json must mirror mandatory negatives")
    if flags.avoid_brands:
        _check_json_for_brands(json_payload)
    return text.strip()
