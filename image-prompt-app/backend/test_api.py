import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_get_images_endpoint():
    """Smoke test for the GET /images endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/images")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_assemble_endpoint_no_key():
    """Test that assemble fails without an API key."""
    # This assumes the test runs in an env without the key set
    # and before any key is provided via the /settings/key endpoint.
    from app import API_KEY_STORE, initialize_openai_client
    original_key = API_KEY_STORE.get("api_key")
    API_KEY_STORE["api_key"] = None
    initialize_openai_client()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/assemble", json={"subject": "test"})

    assert response.status_code == 400
    assert "not initialized" in response.json()["detail"]

    # Restore key
    API_KEY_STORE["api_key"] = original_key
    initialize_openai_client()
