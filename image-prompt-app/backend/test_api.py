from fastapi.testclient import TestClient

from app import API_KEY_STORE, app, initialize_openai_client


def test_get_images_endpoint() -> None:
    """Smoke test for the GET /images endpoint."""
    with TestClient(app) as client:
        response = client.get("/api/images")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_assemble_endpoint_no_key() -> None:
    """Test that assemble fails without an API key."""
    original_key = API_KEY_STORE.get("api_key")
    API_KEY_STORE["api_key"] = None
    initialize_openai_client()

    with TestClient(app) as client:
        response = client.post("/api/assemble", json={"subject": "test"})

    assert response.status_code == 400
    assert "not initialized" in response.json()["detail"]

    API_KEY_STORE["api_key"] = original_key
    initialize_openai_client()
