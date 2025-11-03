from fastapi.testclient import TestClient

from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app  # noqa: E402  (import after path injection)


client = TestClient(app)


def test_health_endpoint_reports_status():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "openai_key" in payload


def test_generate_requires_api_key():
    response = client.post(
        "/api/generate",
        json={
            "topic": "dinosaurs",
            "audience": "kids",
            "age": "6-9",
            "depth": 3,
            "variants": 2,
            "images_per_prompt": 1,
            "mode": "full",
        },
    )
    assert response.status_code == 400
    assert "OPENAI_API_KEY" in response.json()["detail"]
