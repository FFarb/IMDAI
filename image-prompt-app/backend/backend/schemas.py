"""Advisory JSON schemas for pipeline responses."""

RESEARCH_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "analysis": {"type": "string"},
        "highlights": {
            "type": "array",
            "items": {"type": "string"},
        },
        "segments": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["analysis"],
}

SYNTHESIS_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "prompts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "positive": {"type": "string"},
                    "negative": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["positive", "negative"],
            },
        },
        "raw_text": {"type": "string"},
    },
    "required": ["prompts", "raw_text"],
}

__all__ = ["RESEARCH_SCHEMA", "SYNTHESIS_SCHEMA"]
