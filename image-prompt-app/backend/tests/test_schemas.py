import pytest
from jsonschema import validate, ValidationError
from backend.schemas import RESEARCH_SCHEMA, SYNTHESIS_SCHEMA

# Basic valid payloads for testing
VALID_RESEARCH = {
    "references": [{"url": "http://a.com", "title": "t", "type": "gallery"}],
    "designs": [{
        "motifs": ["a"], "composition": ["b"], "line": "regular", "outline": "clean",
        "typography": ["c"], "palette": [{"hex": "#fff", "weight": 1}],
        "mood": ["d"], "hooks": ["e"], "notes": ["f"]
    }],
    "color_distribution": [{"area": "background", "hex": "#000", "weight": 1}],
    "light_distribution": {"direction": "top-down", "key": 0.5, "fill": 0.3, "rim": 0.1, "ambient": 0.1, "zones": [], "notes": ""},
    "gradient_distribution": [{
        "allow": False, "type": "linear", "stops": [{"hex": "#fff", "pos": 0}], "areas": ["a"]
    }]
}

VALID_SYNTHESIS = {
    "prompts": [{
        "positive": "a", "negative": ["b"],
        "palette_distribution": [{"hex": "#000", "weight": 1}],
        "light_distribution": {"direction": "top-down", "key": 0.5, "fill": 0.3, "rim": 0.1, "ambient": 0.1, "zones": [], "notes": ""},
        "gradient_distribution": [{"allow": True, "type": "radial", "stops": [{"hex": "#fff", "pos": 1}], "areas": ["b"]}]
    }]
}

def test_research_schema_valid_payload():
    validate(instance=VALID_RESEARCH, schema=RESEARCH_SCHEMA)

def test_research_schema_invalid_payload():
    invalid_payload = VALID_RESEARCH.copy()
    del invalid_payload["designs"] # 'designs' is a required field
    with pytest.raises(ValidationError):
        validate(instance=invalid_payload, schema=RESEARCH_SCHEMA)

def test_synthesis_schema_valid_payload():
    validate(instance=VALID_SYNTHESIS, schema=SYNTHESIS_SCHEMA)

def test_synthesis_schema_invalid_payload():
    invalid_payload = VALID_SYNTHESIS.copy()
    # 'prompts' must be a list of objects, not strings
    invalid_payload["prompts"] = ["just a string"]
    with pytest.raises(ValidationError):
        validate(instance=invalid_payload, schema=SYNTHESIS_SCHEMA)

def test_gradient_distribution_constraints():
    # Test that a gradient stop requires a 'pos'
    invalid_grad = VALID_RESEARCH.copy()
    invalid_grad["gradient_distribution"][0]["stops"] = [{"hex": "#fff"}]
    with pytest.raises(ValidationError):
        validate(instance=invalid_grad, schema=RESEARCH_SCHEMA)
