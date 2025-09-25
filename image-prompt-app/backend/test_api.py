import json
import os

import pytest
from httpx import ASGITransport, AsyncClient

from app import ETSY_LISTINGS_FILE, app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.anyio
async def test_get_images_endpoint():
    """Smoke test for the GET /images endpoint."""
    async with _client() as ac:
        response = await ac.get("/api/images")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.anyio
async def test_assemble_endpoint_no_key():
    """Test that assemble fails without an API key."""
    # This assumes the test runs in an env without the key set
    # and before any key is provided via the /settings/key endpoint.
    from app import API_KEY_STORE, initialize_openai_client
    original_key = API_KEY_STORE.get("api_key")
    API_KEY_STORE["api_key"] = None
    initialize_openai_client()

    async with _client() as ac:
        response = await ac.post("/api/assemble", json={"subject": "test"})

    assert response.status_code == 400
    assert "not initialized" in response.json()["detail"]

    # Restore key
    API_KEY_STORE["api_key"] = original_key
    initialize_openai_client()


@pytest.mark.anyio
async def test_create_etsy_listing():
    """Ensure Etsy listing payloads are accepted and persisted."""
    # Arrange: create a dummy image so the endpoint can find it
    image_filename = "test-image.png"
    image_path = os.path.join("data", "outputs", image_filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(b"fake image bytes")

    # Remove any previous listing captures
    if os.path.exists(ETSY_LISTINGS_FILE):
        os.remove(ETSY_LISTINGS_FILE)

    payload = {
        "image_path": f"/images/{image_filename}",
        "title": "Galactic Voyager",
        "description": "A vibrant sci-fi illustration",
        "tags": ["sci-fi", "space"],
        "price": 12.5,
    }

    # Act
    async with _client() as ac:
        response = await ac.post("/api/etsy/listings", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["listing"]["title"] == payload["title"]
    assert os.path.exists(ETSY_LISTINGS_FILE)
    with open(ETSY_LISTINGS_FILE, "r", encoding="utf-8") as f:
        persisted = json.load(f)
    assert isinstance(persisted, list)
    assert persisted[-1]["title"] == payload["title"]

    # Cleanup
    if os.path.exists(image_path):
        os.remove(image_path)
    if os.path.exists(ETSY_LISTINGS_FILE):
        os.remove(ETSY_LISTINGS_FILE)
