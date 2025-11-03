"""JSON schema contracts shared with the Responses API."""

RESEARCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "references": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "gallery",
                            "article",
                            "store",
                            "blog",
                            "community",
                            "other",
                        ],
                    },
                    "summary": {"type": "string"},
                },
                "required": ["url", "title", "type"],
            },
        },
        "motifs": {"type": "array", "items": {"type": "string"}},
        "composition": {"type": "array", "items": {"type": "string"}},
        "line": {
            "type": "string",
            "enum": ["ultra-thin", "thin", "regular", "bold"],
        },
        "outline": {
            "type": "string",
            "enum": ["none", "clean", "heavy", "rough"],
        },
        "typography": {"type": "array", "items": {"type": "string"}},
        "palette": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "hex": {"type": "string"},
                    "weight": {"type": "number"},
                },
                "required": ["hex", "weight"],
            },
        },
        "mood": {"type": "array", "items": {"type": "string"}},
        "hooks": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": [
        "references",
        "motifs",
        "composition",
        "line",
        "outline",
        "palette",
    ],
}

SYNTHESIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "positive": {"type": "string"},
                    "negative": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                },
                "required": ["positive", "negative"],
            },
        }
    },
    "required": ["prompts"],
}
