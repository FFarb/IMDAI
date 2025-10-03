"""Integration tests for feature analysis and prompt endpoints."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app import app
from discovery import thumbs
from discovery.router import get_store
from discovery.store import DiscoveryStore


@pytest.fixture(autouse=True)
def disable_external_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('FEATURES_ENABLE_CLIP', 'false')
    monkeypatch.setenv('OCR_ENABLE', 'false')


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    store = DiscoveryStore(tmp_path / 'discovery.sqlite3')
    thumbs.THUMBS_DIR = tmp_path / 'thumbs'
    thumbs.THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _image_bytes(color: tuple[int, int, int], extra: str | None = None) -> bytes:
    image = Image.new('RGB', (256, 256), color=color)
    draw = ImageDraw.Draw(image)
    if extra == 'star':
        points = [
            (128, 20),
            (156, 100),
            (236, 100),
            (172, 148),
            (200, 230),
            (128, 180),
            (56, 230),
            (84, 148),
            (20, 100),
            (100, 100),
        ]
        draw.polygon(points, fill=(255, 220, 80))
    elif extra == 'cloud':
        draw.ellipse((40, 110, 120, 170), fill='white')
        draw.ellipse((90, 90, 190, 170), fill='white')
        draw.rectangle((60, 140, 180, 180), fill='white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def test_feature_analysis_and_prompt_autofill(client: TestClient) -> None:
    response = client.post(
        '/api/discover/search',
        json={'query': 'test', 'adapters': ['local'], 'limit': 10},
    )
    response.raise_for_status()
    session_id = response.json()['session_id']

    files = [
        ('files', ('baby_star.png', _image_bytes((240, 180, 220), 'star'), 'image/png')),
        ('files', ('soft_cloud.png', _image_bytes((180, 220, 255), 'cloud'), 'image/png')),
        ('files', ('disney_logo.png', _image_bytes((200, 200, 200)), 'image/png')),
    ]
    upload = client.post(f'/api/discover/{session_id}/local', files=files)
    upload.raise_for_status()
    assert upload.json()['count'] == 3

    items = client.get(f'/api/discover/{session_id}/items', params={'status': 'result'}).json()['items']
    for item in items:
        select = client.post(
            f'/api/discover/{session_id}/select',
            json={'reference_id': item['id']},
        )
        select.raise_for_status()

    analyze = client.post(
        f'/api/discover/{session_id}/analyze',
        json={'scope': 'selected'},
    )
    analyze.raise_for_status()
    assert analyze.json()['total'] == len(items)

    features = client.get(f'/api/discover/{session_id}/features')
    features.raise_for_status()
    feature_payload = features.json()
    assert set(feature_payload.keys()) == {item['id'] for item in items}

    traits_response = client.get(f'/api/discover/{session_id}/traits')
    traits_response.raise_for_status()
    traits = traits_response.json()
    assert len(traits['palette']) == 6
    assert 0 < len(traits['motifs']) <= 12
    assert all('disney' not in motif.lower() for motif in traits['motifs'])

    autofill = client.post(
        '/api/prompt/autofill',
        json={
            'session_id': session_id,
            'audience_modes': ['Baby', 'Luxury-Inspired'],
            'trait_weights': {'palette': 1.5, 'motifs': 1.2, 'line': 1.0},
        },
    )
    autofill.raise_for_status()
    payload = autofill.json()
    text = payload['prompt_text']
    assert 'transparent background' in text
    assert 'Negative: photo-realism' in text
    prompt_json = payload['prompt_json']
    assert prompt_json['audience_modes'] == ['Baby', 'Luxury-Inspired']
    assert prompt_json['negative'] == 'photo-realism, photographic textures, noise, background patterns, brand logos, trademark words'
