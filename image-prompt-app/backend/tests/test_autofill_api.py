from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from app import app
from server.autofill.models import AUTOFILL_JSON_SCHEMA
from server.autofill.providers import ProviderResult
from server.autofill.router import reset_provider
from server.autofill.validators import MANDATORY_NEGATIVE


class DummyProvider:
    allow_web = True

    def __init__(self) -> None:
        self.payload: Dict[str, Any] = {}

    def research(
        self, system_prompt: str, user_prompt: str, use_web: bool, max_attempts: int = 3
    ) -> ProviderResult:
        return ProviderResult(payload=self.payload, used_web=use_web)


@pytest.fixture()
def dummy_provider() -> DummyProvider:
    provider = DummyProvider()
    reset_provider(provider)
    yield provider
    reset_provider(None)


@pytest.fixture()
def client(dummy_provider: DummyProvider) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def valid_payload() -> Dict[str, Any]:
    return {
        "palette": [
            {"hex": "#ffcc00", "weight": 0.3},
            {"hex": "#ffeeaa", "weight": 0.2},
            {"hex": "#112233", "weight": 0.2},
            {"hex": "#445566", "weight": 0.15},
            {"hex": "#778899", "weight": 0.15},
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
        ],
        "master_prompt_text": (
            "Minimal safari nursery scene, transparent background, no shadows, no gradients, "
            "no textures, clean vector edges, centered standalone composition"
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


def _assemble_schema_payload(body: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(body["traits"])
    payload["master_prompt_text"] = body["master_prompt_text"]
    payload["master_prompt_json"] = body["master_prompt_json"]
    return payload


def _assert_matches_schema(payload: Dict[str, Any]) -> None:
    required = set(AUTOFILL_JSON_SCHEMA["required"])
    assert required.issubset(payload)

    palette = payload["palette"]
    assert isinstance(palette, list)
    assert 5 <= len(palette) <= 7
    for color in palette:
        assert color["hex"].startswith("#")
        assert 0 <= color["weight"] <= 1

    motifs = payload["motifs"]
    assert isinstance(motifs, list)
    assert 8 <= len(motifs) <= 12

    assert payload["line_weight"] in {"thin", "regular", "bold"}
    assert payload["outline"] in {"clean", "rough"}
    assert isinstance(payload["typography"], list)
    assert isinstance(payload["composition"], list)
    assert isinstance(payload["audience"], str)
    assert isinstance(payload["age"], str)
    assert isinstance(payload["mood"], list)
    assert isinstance(payload["seed_examples"], list)
    assert isinstance(payload["negative"], list)

    sources = payload["sources"]
    if sources is not None:
        for source in sources:
            assert "title" in source and "url" in source

    master_prompt = payload["master_prompt_json"]
    for key in [
        "subject",
        "palette",
        "motifs",
        "line",
        "outline",
        "typography",
        "composition",
        "mood",
        "negative",
    ]:
        assert key in master_prompt


def test_research_success(client: TestClient, dummy_provider: DummyProvider) -> None:
    dummy_provider.payload = valid_payload()
    response = client.post(
        "/api/autofill/research",
        json={"topic": "baby safari", "audience": "kids", "age": "0–2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["traits"]["audience"] == "kids"
    assert len(body["traits"]["palette"]) == 5
    assert "transparent background" in body["master_prompt_text"].lower()
    assert body["master_prompt_json"]["palette"] == [color["hex"].upper() for color in body["traits"]["palette"]]


def test_research_schema_compliance(client: TestClient, dummy_provider: DummyProvider) -> None:
    dummy_provider.payload = valid_payload()
    response = client.post(
        "/api/autofill/research",
        json={"topic": "baby safari", "audience": "kids", "age": "0–2"},
    )
    assert response.status_code == 200
    body = response.json()
    _assert_matches_schema(_assemble_schema_payload(body))


def test_research_invalid_payload(client: TestClient, dummy_provider: DummyProvider) -> None:
    payload = valid_payload()
    payload.pop("master_prompt_text")
    dummy_provider.payload = payload
    response = client.post(
        "/api/autofill/research",
        json={"topic": "baby safari", "audience": "kids", "age": "0–2"},
    )
    assert response.status_code == 422
    assert "master_prompt_text" in response.json()["detail"]


def test_one_click_generate(monkeypatch: pytest.MonkeyPatch, dummy_provider: DummyProvider) -> None:
    dummy_provider.payload = valid_payload()

    async def fake_dispatch(request, payload):  # type: ignore[no-untyped-def]
        assert payload["n"] == 3
        assert payload["prompt"]["params"] == {"size": "1536x1024", "quality": "low"}
        return [
            {"image_path": "/images/test.png", "prompt": payload["prompt"]},
            {"image_path": "/images/test2.png", "prompt": payload["prompt"]},
        ]

    monkeypatch.setattr("server.autofill.router._dispatch_image_generation", fake_dispatch)

    with TestClient(app) as client:
        response = client.post(
            "/api/autofill/one-click",
            json={"topic": "baby safari", "audience": "kids", "age": "0–2", "images_n": 3},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["autofill"]["traits"]["audience"] == "kids"
    assert len(body["images"]) == 2
