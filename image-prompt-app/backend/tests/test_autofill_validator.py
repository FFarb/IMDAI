import math
from typing import Dict

import pytest

from server.autofill.models import ResearchFlags
from server.autofill.validators import (
    MANDATORY_NEGATIVE,
    PRINT_READY_CONSTANTS,
    AutofillValidationError,
    validate_autofill_payload,
    validate_master_prompt,
)


@pytest.fixture()
def sample_payload() -> Dict:
    return {
        "palette": [
            {"hex": "#ffcc00", "weight": 0.4},
            {"hex": "#FFCC00", "weight": 0.1},
            {"hex": "#112233", "weight": 0.2},
            {"hex": "#445566", "weight": 0.1},
            {"hex": "#778899", "weight": 0.1},
            {"hex": "#AABBCC", "weight": 0.1},
        ],
        "motifs": [
            "cloud",
            "star",
            "moon",
            "sun",
            "sparkle",
            "planet",
            "animal",
            "pattern",
            "kawaii",
            "bubble",
            "leaf",
            "toy",
        ],
        "line_weight": "thin",
        "outline": "clean",
        "typography": ["rounded sans", "minimal lettering"],
        "composition": ["centered", "minimal frame"],
        "audience": "kids",
        "age": "0–2",
        "mood": ["soft", "playful"],
        "seed_examples": [
            "smiling baby animal sitting in the center",
            "floating pastel safari icons",
        ],
        "negative": MANDATORY_NEGATIVE.copy(),
        "sources": [
            {"title": "Example", "url": "https://example.com"},
            {"title": "Gallery", "url": "https://gallery.example.com"},
        ],
        "master_prompt_text": (
            "Minimal safari nursery scene, transparent background, no shadows, no gradients, "
            "no textures, clean vector edges, centered standalone composition, pastel palette"
        ),
        "master_prompt_json": {
            "subject": "Minimal safari nursery scene",
            "palette": ["#FFCC00", "#112233"],
            "motifs": [
                "cloud",
                "star",
                "moon",
                "sun",
                "sparkle",
                "planet",
                "animal",
                "pattern",
                "kawaii",
                "bubble",
                "leaf",
                "toy",
            ],
            "line": "thin",
            "outline": "clean",
            "typography": ["rounded sans", "minimal lettering"],
            "composition": ["centered", "minimal frame"],
            "mood": ["soft", "playful"],
            "negative": MANDATORY_NEGATIVE.copy(),
            "audience": "kids",
            "age": "0–2",
        },
    }


def test_palette_normalization(sample_payload: Dict) -> None:
    flags = ResearchFlags()
    traits = validate_autofill_payload(sample_payload, flags, max_sources=5)
    assert len(traits.palette) == 5
    total_weight = sum(color.weight for color in traits.palette)
    assert math.isclose(total_weight, 1.0, rel_tol=1e-3)


def test_motifs_brand_filtering(sample_payload: Dict) -> None:
    payload = sample_payload.copy()
    payload["motifs"] = [
        "cloud",
        "nike swoosh",
        "moon",
        "starbucks cup",
        "sparkle",
        "planet",
        "animal",
        "pattern",
        "kawaii",
        "bubble",
        "leaf",
        "toy",
        "extra",
    ]
    flags = ResearchFlags(avoid_brands=True)
    traits = validate_autofill_payload(payload, flags, max_sources=8)
    assert "nike swoosh" not in traits.motifs
    assert "starbucks cup" not in traits.motifs
    assert len(traits.motifs) == 10


def test_kids_unsafe_raises(sample_payload: Dict) -> None:
    payload = sample_payload.copy()
    payload["motifs"] = [
        "cloud",
        "moon",
        "gun",
        "star",
        "sparkle",
        "planet",
        "animal",
        "pattern",
    ]
    flags = ResearchFlags(kids_safe=True)
    with pytest.raises(AutofillValidationError):
        validate_autofill_payload(payload, flags, max_sources=5)


def test_master_prompt_contains_required_phrases(sample_payload: Dict) -> None:
    flags = ResearchFlags()
    traits = validate_autofill_payload(sample_payload, flags, max_sources=5)
    prompt_text = validate_master_prompt(traits, sample_payload, flags)
    for phrase in PRINT_READY_CONSTANTS:
        assert phrase in prompt_text.lower()


def test_master_prompt_brand_rejection(sample_payload: Dict) -> None:
    payload = sample_payload.copy()
    payload["master_prompt_text"] = (
        "Transparent background with clean vector edges featuring a Disney castle, "
        "no shadows, no gradients, no textures, centered standalone composition"
    )
    flags = ResearchFlags(avoid_brands=True)
    traits = validate_autofill_payload(payload, flags, max_sources=5)
    with pytest.raises(AutofillValidationError):
        validate_master_prompt(traits, payload, flags)
