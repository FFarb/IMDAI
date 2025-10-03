"""Utilities for composing print-ready master prompts."""
from __future__ import annotations

from typing import Mapping, Sequence

from .models import DatasetTraits, PaletteColor

_BASE_CONSTRAINTS = [
    "transparent background",
    "no shadows",
    "no gradients",
    "no textures",
    "clean vector edges",
    "centered standalone composition",
]

_BASE_NEGATIVE = (
    "photo-realism, photographic textures, noise, background patterns, brand logos, trademark words"
)

_AUDIENCE_MOODS = {
    "Baby": "soft, cozy, nurturing warmth",
    "Toddler": "playful, friendly energy",
    "Baby-Mama": "calm, comforting sophistication",
    "Luxury-Inspired": "premium minimal minimalism",
}

_LINE_DESCRIPTORS = {
    "thin": "delicate thin line art",
    "regular": "balanced medium line work",
    "bold": "bold, confident outlines",
}

_OUTLINE_DESCRIPTORS = {
    "clean": "ultra clean outline clarity",
    "rough": "slightly hand-drawn outline texture",
}


def _palette_text(palette: Sequence[PaletteColor]) -> str:
    return ", ".join(f"{entry.hex} ({entry.weight:.2f})" for entry in palette)


def _motifs_subject(traits: DatasetTraits, audience_modes: Sequence[str]) -> str:
    motifs = traits.motifs[:6] if traits.motifs else ["abstract shapes"]
    audience = ", ".join(audience_modes) if audience_modes else "broad audience"
    return f"vector iconography for {audience} featuring {', '.join(motifs)}"


def _weight_modifier(value: float | None) -> str:
    if value is None:
        return "balanced"
    if value >= 1.6:
        return "strong focus on"
    if value <= 0.7:
        return "light touch of"
    return "balanced"


def _mood_line(audience_modes: Sequence[str], motifs: Sequence[str]) -> str:
    moods = [_AUDIENCE_MOODS.get(mode, "refined minimalism") for mode in audience_modes]
    if not moods:
        moods.append("refined minimalism")
    primary_mood = ", ".join(dict.fromkeys(moods))
    highlight = ", ".join(motifs[:3]) if motifs else "soft geometry"
    return f"Mood: {primary_mood} with hints of {highlight}."


def build_master_prompt(
    traits: DatasetTraits,
    audience_modes: Sequence[str],
    trait_weights: Mapping[str, float] | None = None,
) -> dict[str, object]:
    trait_weights = trait_weights or {}
    subject_line = _motifs_subject(traits, audience_modes)
    palette_modifier = _weight_modifier(trait_weights.get("palette"))
    motif_modifier = _weight_modifier(trait_weights.get("motifs"))
    line_descriptor = _LINE_DESCRIPTORS.get(traits.line_weight, "balanced medium line work")
    outline_descriptor = _OUTLINE_DESCRIPTORS.get(traits.outline, "ultra clean outline clarity")

    if traits.typography:
        typography_text = ", ".join(traits.typography)
    else:
        typography_text = "avoid any text or lettering"

    composition_text = ", ".join(traits.composition) if traits.composition else "center-focused"
    palette_text = _palette_text(traits.palette)

    lines = [
        ", ".join(_BASE_CONSTRAINTS) + ".",
        f"Subject & Motifs ({motif_modifier}): {subject_line}.",
        f"Palette ({palette_modifier}): {palette_text}.",
        f"Line & Outline: {line_descriptor} with {outline_descriptor}.",
        f"Typography: {typography_text}.",
        f"Composition: {composition_text}.",
        _mood_line(audience_modes, traits.motifs),
        f"Negative: {_BASE_NEGATIVE}.",
    ]
    prompt_text = "\n".join(lines)

    prompt_json = {
        "audience_modes": list(audience_modes),
        "palette": [entry.model_dump() for entry in traits.palette],
        "motifs": traits.motifs,
        "line": traits.line_weight,
        "outline": traits.outline,
        "typography": traits.typography if traits.typography else ["avoid text"],
        "composition": traits.composition if traits.composition else ["centered"],
        "constraints": list(_BASE_CONSTRAINTS),
        "mood": _mood_line(audience_modes, traits.motifs).replace("Mood: ", ""),
        "negative": _BASE_NEGATIVE,
    }
    return {"prompt_text": prompt_text, "prompt_json": prompt_json}
