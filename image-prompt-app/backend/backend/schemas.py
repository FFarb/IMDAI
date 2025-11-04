"""Shared JSON Schemas for model outputs."""

HEX_COLOR = {
    "type": "string",
    "pattern": "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
}

WEIGHT_NUMBER = {
    "type": "number",
    "minimum": 0,
}

PALETTE_ITEM = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "hex": HEX_COLOR,
        "weight": WEIGHT_NUMBER,
    },
    "required": ["hex", "weight"],
}

COLOR_DISTRIBUTION_ITEM = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "area": {
            "type": "string",
        },
        "hex": HEX_COLOR,
        "weight": WEIGHT_NUMBER,
    },
    "required": ["area", "hex", "weight"],
}

LIGHT_DISTRIBUTION = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "direction": {"type": "string"},
        "key": WEIGHT_NUMBER,
        "fill": WEIGHT_NUMBER,
        "rim": WEIGHT_NUMBER,
        "ambient": WEIGHT_NUMBER,
        "zones": {
            "type": "array",
            "items": {"type": "string"},
        },
        "notes": {"type": "string"},
    },
    "required": ["direction"],
}

GRADIENT_STOP = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "hex": HEX_COLOR,
        "pos": {"type": "number"},
        "weight": WEIGHT_NUMBER,
    },
    "required": ["hex", "pos"],
}

GRADIENT_ITEM = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "allow": {"type": "boolean"},
        "type": {"type": "string", "enum": ["linear", "radial", "conic"]},
        "stops": {"type": "array", "items": GRADIENT_STOP, "minItems": 1},
        "areas": {"type": "array", "items": {"type": "string"}},
        "angle": {"type": "number"},
        "center": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
            },
        },
        "vector_approximation_steps": {"type": "integer", "minimum": 0},
    },
    "required": ["allow", "type", "stops", "areas"],
}

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
        "designs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "motifs": {"type": "array", "items": {"type": "string"}},
                    "composition": {"type": "array", "items": {"type": "string"}},
                    "line": {"type": "string"},
                    "outline": {"type": "string"},
                    "typography": {"type": "array", "items": {"type": "string"}},
                    "palette": {"type": "array", "items": PALETTE_ITEM},
                    "mood": {"type": "array", "items": {"type": "string"}},
                    "hooks": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "motifs",
                    "composition",
                    "line",
                    "outline",
                    "typography",
                    "palette",
                    "mood",
                    "hooks",
                    "notes",
                ],
            },
        },
        "color_distribution": {
            "type": "array",
            "items": COLOR_DISTRIBUTION_ITEM,
        },
        "light_distribution": LIGHT_DISTRIBUTION,
        "gradient_distribution": {
            "type": "array",
            "items": GRADIENT_ITEM,
        },
        "palette": {
            "type": "array",
            "items": PALETTE_ITEM,
        },
        "notes": {"type": "string"},
    },
    "required": [
        "references",
        "designs",
        "color_distribution",
        "light_distribution",
        "gradient_distribution",
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
                    "negative": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "notes": {"type": "string"},
                    "palette_distribution": {
                        "type": "array",
                        "items": PALETTE_ITEM,
                    },
                    "light_distribution": LIGHT_DISTRIBUTION,
                    "gradient_distribution": {
                        "type": "array",
                        "items": GRADIENT_ITEM,
                    },
                    "constraints": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "transparent_background": {"type": "boolean"},
                            "vector_safe": {"type": "boolean"},
                            "gradient_mode": {
                                "type": "string",
                                "enum": ["approximate", "true-gradients"],
                            },
                        },
                    },
                },
                "required": [
                    "positive",
                    "negative",
                    "palette_distribution",
                    "light_distribution",
                    "gradient_distribution",
                ],
            },
        },
        "metadata": {"type": "object"},
    },
    "required": ["prompts"],
}


__all__ = ["RESEARCH_SCHEMA", "SYNTHESIS_SCHEMA"]
