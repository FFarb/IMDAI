from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app import app

MOCK_RESEARCH_TEXT = """
OVERVIEW: Friendly dinosaurs teaching science in colourful classrooms.
- Encourage curiosity and playful discovery.
COLOR PALETTE: mint greens, sky blues, butter yellows.
NEGATIVE GUIDANCE: avoid realistic gore, no sharp teeth.
""".strip()

MOCK_SYNTHESIS_TEXT = """
PROMPT 1:
Positive: whimsical classroom mural of cartoon dinosaurs teaching science experiments with beakers, vivid chalk illustrations, joyful smiles, mint green and sky blue palette, soft glowing light, storybook illustration style
Negative: gore, horror, fangs, clutter
Notes: emphasise educational props and inclusive characters

PROMPT 2:
Positive: panoramic poster of dinosaur friends guiding kids through constellations, gentle gradients, magical twilight lighting, painterly textures, friendly faces and clear typography
Negative: violence, photorealism, chaotic layout
Notes: ensure accessibility with bold labels
""".strip()


@pytest.fixture
def client():
    yield TestClient(app)


@patch("backend.research.has_valid_key", return_value=True)
@patch("backend.research.get_openai_client")
def test_research_endpoint_success(mock_get_client, mock_has_key, client):
    mock_choice = SimpleNamespace(message=SimpleNamespace(content=MOCK_RESEARCH_TEXT))
    mock_resp = SimpleNamespace(choices=[mock_choice])

    class _Completions:
        def create(self, **kwargs):
            return mock_resp

    class _Chat:
        completions = _Completions()

    mock_client = SimpleNamespace(chat=_Chat())
    mock_get_client.return_value = mock_client

    response = client.post(
        "/api/research",
        json={"topic": "a", "audience": "b", "age": "c", "depth": 3},
    )

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["analysis"].startswith("OVERVIEW")
    assert any("gore" in highlight for highlight in payload["highlights"])


@patch("backend.synthesize.has_valid_key", return_value=True)
@patch("backend.synthesize.get_openai_client")
def test_synthesize_endpoint_success(mock_get_client, mock_has_key, client):
    mock_choice = SimpleNamespace(message=SimpleNamespace(content=MOCK_SYNTHESIS_TEXT))
    mock_resp = SimpleNamespace(choices=[mock_choice])

    class _Completions:
        def create(self, **kwargs):
            return mock_resp

    class _Chat:
        completions = _Completions()

    mock_client = SimpleNamespace(chat=_Chat())
    mock_get_client.return_value = mock_client

    response = client.post(
        "/api/synthesize",
        json={
            "research_text": MOCK_RESEARCH_TEXT,
            "audience": "a",
            "age": "b",
            "variants": 2,
        },
    )

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert len(payload["prompts"]) == 2
    assert "whimsical classroom" in payload["prompts"][0]["positive"].lower()
    assert "gore" in ", ".join(payload["prompts"][0]["negative"]).lower()


@patch("backend.images.has_valid_key", return_value=True)
@patch("backend.images.get_openai_client")
def test_images_endpoint_gradient_policy(mock_get_client, mock_has_key, client):
    mock_image_data = SimpleNamespace(url="http://example.com/image.png", b64_json=None)
    mock_response = SimpleNamespace(data=[mock_image_data])

    class _Images:
        def generate(self, **kwargs):
            return mock_response

    mock_client = SimpleNamespace(images=_Images())
    mock_client.images.generate = MagicMock(return_value=mock_response)
    mock_get_client.return_value = mock_client

    # Test with ALLOW_TRUE_GRADIENTS=False
    with patch("backend.images.ALLOW_TRUE_GRADIENTS", False):
        response = client.post(
            "/api/images",
            json={"prompt_positive": "a", "prompt_negative": [], "n": 1},
        )
        assert response.status_code == 200, response.json()
        _, kwargs = mock_client.images.generate.call_args
        assert "gradients" in kwargs["prompt"]
        assert "textures" in kwargs["prompt"]

    # Test with ALLOW_TRUE_GRADIENTS=True
    with patch("backend.images.ALLOW_TRUE_GRADIENTS", True):
        response = client.post(
            "/api/images",
            json={"prompt_positive": "a", "prompt_negative": ["test"], "n": 1},
        )
        assert response.status_code == 200, response.json()
        _, kwargs = mock_client.images.generate.call_args
        assert "gradients" not in kwargs["prompt"]
        assert "test" in kwargs["prompt"]
