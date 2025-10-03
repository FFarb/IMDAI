"""Pydantic models used by the autofill research endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, conlist, constr


class ResearchFlags(BaseModel):
    """Toggles that control how research is performed."""

    model_config = ConfigDict(extra="forbid")

    use_web: bool = True
    avoid_brands: bool = True
    kids_safe: bool = True


class ResearchRequest(BaseModel):
    """Incoming request for the autofill research endpoint."""

    model_config = ConfigDict(extra="forbid")

    topic: constr(min_length=1, strip_whitespace=True)
    audience: constr(min_length=1, strip_whitespace=True)
    age: constr(min_length=1, strip_whitespace=True)
    images_n: int = Field(4, ge=1, le=8)
    flags: ResearchFlags = Field(default_factory=ResearchFlags)


class PaletteColor(BaseModel):
    """A palette entry returned by research."""

    model_config = ConfigDict(extra="forbid")

    hex: constr(pattern=r"^#([A-Fa-f0-9]{6})$")
    weight: float


class SourceLink(BaseModel):
    """Reference to public sources used during research."""

    model_config = ConfigDict(extra="forbid")

    title: constr(min_length=1, strip_whitespace=True)
    url: HttpUrl


LineWeight = Literal["thin", "regular", "bold"]
OutlineQuality = Literal["clean", "rough"]
CompositionLabel = Literal["centered", "single character", "subtle lattice", "grid", "minimal frame"]


class DatasetTraits(BaseModel):
    """Structured traits describing the researched dataset."""

    model_config = ConfigDict(extra="forbid")

    palette: conlist(PaletteColor, min_length=5, max_length=7)
    motifs: conlist(constr(min_length=1, strip_whitespace=True), min_length=8, max_length=12)
    line_weight: LineWeight
    outline: OutlineQuality
    typography: conlist(constr(min_length=1, strip_whitespace=True), max_length=3)
    composition: conlist(CompositionLabel, min_length=1)
    audience: constr(min_length=1)
    age: constr(min_length=1)
    mood: conlist(constr(min_length=1, strip_whitespace=True), max_length=3)
    negative: conlist(constr(min_length=1, strip_whitespace=True), min_length=1)
    seed_examples: conlist(constr(min_length=1, strip_whitespace=True), min_length=2, max_length=3)
    sources: Optional[conlist(SourceLink, min_length=1, max_length=10)] = None


class AutofillResponse(BaseModel):
    """Full response returned by research endpoints."""

    model_config = ConfigDict(extra="forbid")

    traits: DatasetTraits
    master_prompt_text: constr(min_length=1)
    master_prompt_json: Dict[str, Any]


AUTOFILL_JSON_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "palette",
        "motifs",
        "line_weight",
        "outline",
        "typography",
        "composition",
        "audience",
        "age",
        "mood",
        "seed_examples",
        "negative",
        "sources",
        "master_prompt_text",
        "master_prompt_json",
    ],
    "properties": {
        "palette": {
            "type": "array",
            "minItems": 5,
            "maxItems": 7,
            "items": {
                "type": "object",
                "required": ["hex", "weight"],
                "properties": {
                    "hex": {
                        "type": "string",
                        "pattern": "^#([A-Fa-f0-9]{6})$",
                    },
                    "weight": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                },
                "additionalProperties": False,
            },
        },
        "motifs": {
            "type": "array",
            "minItems": 8,
            "maxItems": 12,
            "items": {"type": "string", "minLength": 1},
        },
        "line_weight": {
            "type": "string",
            "enum": ["thin", "regular", "bold"],
        },
        "outline": {
            "type": "string",
            "enum": ["clean", "rough"],
        },
        "typography": {
            "type": "array",
            "maxItems": 3,
            "items": {"type": "string"},
        },
        "composition": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "centered",
                    "single character",
                    "subtle lattice",
                    "grid",
                    "minimal frame",
                ],
            },
        },
        "audience": {"type": "string", "minLength": 1},
        "age": {"type": "string", "minLength": 1},
        "mood": {
            "type": "array",
            "maxItems": 3,
            "items": {"type": "string"},
        },
        "seed_examples": {
            "type": "array",
            "minItems": 2,
            "maxItems": 3,
            "items": {"type": "string", "minLength": 1},
        },
        "negative": {
            "type": "array",
            "minItems": 6,
            "items": {"type": "string", "minLength": 1},
        },
        "sources": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "required": ["title", "url"],
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "url": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            },
            "maxItems": 10,
        },
        "master_prompt_text": {"type": "string", "minLength": 1},
        "master_prompt_json": {
            "type": "object",
            "required": [
                "subject",
                "palette",
                "motifs",
                "line",
                "outline",
                "typography",
                "composition",
                "mood",
                "negative",
            ],
            "properties": {
                "subject": {"type": "string"},
                "palette": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^#([A-Fa-f0-9]{6})$"},
                },
                "motifs": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
                "line": {
                    "type": "string",
                    "enum": ["thin", "regular", "bold"],
                },
                "outline": {
                    "type": "string",
                    "enum": ["clean", "rough"],
                },
                "typography": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "composition": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "centered",
                            "single character",
                            "subtle lattice",
                            "grid",
                            "minimal frame",
                        ],
                    },
                },
                "mood": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "negative": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}
