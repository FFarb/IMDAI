import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from backend.app import app

# A sample valid response for the research endpoint, matching the new schema
MOCK_RESEARCH_RESPONSE = {
    "references": [{"url": "http://a.com", "title": "t", "type": "gallery"}],
    "designs": [{"motifs": ["a"], "composition": ["b"], "line": "regular", "outline": "clean", "typography": ["c"], "palette": [{"hex": "#fff", "weight": 1}], "mood": ["d"], "hooks": ["e"], "notes": ["f"]}],
    "palette": [],
    "notes": "Some notes.",
    "color_distribution": [{"area": "background", "hex": "#000", "weight": 1}],
    "light_distribution": {"direction": "top-down", "key": 0.5, "fill": 0.3, "rim": 0.1, "ambient": 0.1, "zones": [], "notes": ""},
    "gradient_distribution": [{"allow": False, "type": "linear", "stops": [{"hex": "#fff", "pos": 0}], "areas": ["a"]}]
}

# A sample valid response for the synthesis endpoint
MOCK_SYNTHESIS_RESPONSE = {
    "prompts": [{"positive": "a", "negative": ["b"], "palette_distribution": [{"hex": "#000", "weight": 1}], "light_distribution": {"direction": "top-down", "key": 0.5, "fill": 0.3, "rim": 0.1, "ambient": 0.1, "zones": [], "notes": ""}, "gradient_distribution": [{"allow": True, "type": "radial", "stops": [{"hex": "#fff", "pos": 1}], "areas": ["b"]}]}]
}

@pytest.fixture
def client():
    yield TestClient(app)

@patch('backend.research.has_valid_key', return_value=True)
@patch('backend.research.get_openai_client')
def test_research_endpoint_success(mock_get_client, mock_has_key, client):
    mock_payload = json.dumps(MOCK_RESEARCH_RESPONSE)

    mock_choice = SimpleNamespace(message=SimpleNamespace(content=mock_payload))
    mock_resp = SimpleNamespace(choices=[mock_choice])

    class _Completions:
        def create(self, **kwargs): return mock_resp

    class _Chat:
        completions = _Completions()

    mock_client = SimpleNamespace(chat=_Chat())
    mock_get_client.return_value = mock_client

    response = client.post("/api/research", json={
        "topic": "a",
        "audience": "b",
        "age": "c",
        "depth": 3
    })

    assert response.status_code == 200, response.json()
    assert response.json()["designs"][0]["motifs"] == ["a"]


@patch('backend.synthesize.has_valid_key', return_value=True)
@patch('backend.synthesize.get_openai_client')
def test_synthesize_endpoint_success(mock_get_client, mock_has_key, client):
    mock_payload = json.dumps(MOCK_SYNTHESIS_RESPONSE)

    mock_choice = SimpleNamespace(message=SimpleNamespace(content=mock_payload))
    mock_resp = SimpleNamespace(choices=[mock_choice])

    class _Completions:
        def create(self, **kwargs): return mock_resp

    class _Chat:
        completions = _Completions()

    mock_client = SimpleNamespace(chat=_Chat())
    mock_get_client.return_value = mock_client

    response = client.post("/api/synthesize", json={
        "research": MOCK_RESEARCH_RESPONSE,
        "audience": "a",
        "age": "b",
        "variants": 1
    })

    assert response.status_code == 200, response.json()
    assert response.json()["prompts"][0]["positive"] == "a"


@patch('backend.images.has_valid_key', return_value=True)
@patch('backend.images.get_openai_client')
def test_images_endpoint_gradient_policy(mock_get_client, mock_has_key, client):
    mock_image_data = SimpleNamespace(url="http://example.com/image.png", b64_json=None)
    mock_response = SimpleNamespace(data=[mock_image_data])

    class _Images:
        def generate(self, **kwargs): return mock_response

    mock_client = SimpleNamespace(images=_Images())
    mock_client.images.generate = MagicMock(return_value=mock_response)
    mock_get_client.return_value = mock_client

    # Test with ALLOW_TRUE_GRADIENTS=False
    with patch('backend.images.ALLOW_TRUE_GRADIENTS', False):
        response = client.post("/api/images", json={"prompt_positive": "a", "prompt_negative": [], "n": 1})
        assert response.status_code == 200, response.json()
        args, kwargs = mock_client.images.generate.call_args
        assert "gradients" in kwargs['prompt']
        assert "textures" in kwargs['prompt']

    # Test with ALLOW_TRUE_GRADIENTS=True
    with patch('backend.images.ALLOW_TRUE_GRADIENTS', True):
        response = client.post("/api/images", json={"prompt_positive": "a", "prompt_negative": ["test"], "n": 1})
        assert response.status_code == 200, response.json()
        args, kwargs = mock_client.images.generate.call_args
        assert "gradients" not in kwargs['prompt']
        assert "test" in kwargs['prompt']
