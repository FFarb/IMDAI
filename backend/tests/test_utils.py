import pytest
from backend.utils.json_sanitize import extract_json_text, parse_model_json

def test_extract_json_text_with_fences():
    raw_text = '```json\n{"key": "value"}\n```'
    assert extract_json_text(raw_text) == '{"key": "value"}'

def test_extract_json_text_without_fences():
    raw_text = '{"key": "value"}'
    assert extract_json_text(raw_text) == '{"key": "value"}'

def test_extract_json_text_with_bom():
    raw_text = '\ufeff{"key": "value"}'
    # Note: extract_json_text doesn't remove the BOM, parse_model_json does
    assert extract_json_text(raw_text) == '\ufeff{"key": "value"}'

def test_parse_model_json_removes_bom_and_nul():
    raw_text = '\ufeff{"key": "value"}\x00'
    assert parse_model_json(raw_text) == {"key": "value"}

def test_parse_model_json_handles_fences_and_cleaning():
    raw_text = '```json\n\ufeff{"key": "value with\x00 null"}\n```'
    assert parse_model_json(raw_text) == {"key": "value with null"}

def test_parse_model_json_raises_error_on_invalid_json():
    raw_text = '{"key": "value",}'
    with pytest.raises(Exception):
        parse_model_json(raw_text)
