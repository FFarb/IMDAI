from fastapi.testclient import TestClient

from app import app


def test_get_meta_options_structure() -> None:
    client = TestClient(app)
    response = client.get("/api/meta/options")
    assert response.status_code == 200
    data = response.json()
    assert "audiences" in data and isinstance(data["audiences"], list)
    assert "ages" in data and isinstance(data["ages"], list)
    assert "default_flags" in data and isinstance(data["default_flags"], dict)
    assert data["default_flags"]["use_web"] in {True, False}
    assert "research_models" in data and "gpt-4.1" in data["research_models"]
    assert "image_models" in data and data["image_models"], "image models should not be empty"
    assert any(option == "custom" for option in data["audiences"])
    assert any(option == "custom" for option in data["ages"])
