import pytest
from jsonschema import ValidationError, validate

from backend.schemas import RESEARCH_SCHEMA, SYNTHESIS_SCHEMA


def test_research_schema_accepts_plain_text_payload():
    payload = {
        "analysis": "Overview and guidance.",
        "highlights": ["Keep colours soft", "Avoid gore"],
        "segments": ["OVERVIEW: ...", "NEGATIVES: ..."],
    }
    validate(instance=payload, schema=RESEARCH_SCHEMA)


def test_research_schema_requires_analysis():
    with pytest.raises(ValidationError):
        validate(instance={"highlights": []}, schema=RESEARCH_SCHEMA)


def test_synthesis_schema_accepts_prompt_blocks():
    payload = {
        "raw_text": "PROMPT 1:\nPositive: Example\nNegative: none",
        "prompts": [
            {
                "positive": "Example prompt",
                "negative": ["gore", "noise"],
                "notes": "Keep it friendly",
            }
        ],
    }
    validate(instance=payload, schema=SYNTHESIS_SCHEMA)


def test_synthesis_schema_requires_prompts():
    with pytest.raises(ValidationError):
        validate(instance={"raw_text": ""}, schema=SYNTHESIS_SCHEMA)
