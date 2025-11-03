import base64
import os
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

import app as app_module


class FakeImagesClient:
    def __init__(self, responses: List[Any]) -> None:
        self.responses = responses
        self.calls: List[Dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(data=self.responses)


@pytest.fixture()
def image_client() -> tuple[TestClient, FakeImagesClient]:
    original_client = app_module.client
    fake_image = SimpleNamespace(
        b64_json=base64.b64encode(b"test-image-bytes").decode("ascii"),
        url=None,
    )
    fake_images = FakeImagesClient([fake_image])
    fake_client = SimpleNamespace(images=fake_images)
    app_module.client = fake_client  # type: ignore[assignment]

    with TestClient(app_module.app) as test_client:
        yield test_client, fake_images

    # Cleanup generated files and restore original client
    output_dir = os.path.join("data", "outputs")
    if os.path.isdir(output_dir):
        for filename in os.listdir(output_dir):
            if filename.startswith("test_image_api"):
                try:
                    os.remove(os.path.join(output_dir, filename))
                except OSError:
                    pass
    app_module.client = original_client  # type: ignore[assignment]


def test_image_endpoint_returns_saved_files(
    monkeypatch: pytest.MonkeyPatch, image_client: tuple[TestClient, FakeImagesClient]
) -> None:
    client, fake_images = image_client
    timestamp = "test_image_api"
    monkeypatch.setattr(app_module, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda fmt: timestamp)))

    payload = {
        "prompt": {
            "positive": "playful pastel safari stickers",
            "negative": "",
            "params": {"size": "1536x1024", "quality": "low"},
        },
        "n": 1,
    }

    response = client.post("/api/image", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    entry = body[0]
    assert entry["prompt"]["params"]["size"] == "1536x1024"
    assert entry["prompt"]["params"]["quality"] == "low"
    assert fake_images.calls[0]["model"] == "gpt-image-1"

    image_filename = entry["image_path"].split("/")[-1]
    output_dir = os.path.join("data", "outputs")
    assert os.path.exists(os.path.join(output_dir, image_filename))
    assert os.path.exists(os.path.join(output_dir, image_filename.replace(".png", ".json")))

    # Cleanup test artifacts
    os.remove(os.path.join(output_dir, image_filename))
    os.remove(os.path.join(output_dir, image_filename.replace(".png", ".json")))
