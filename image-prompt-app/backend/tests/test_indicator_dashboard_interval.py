"""Tests for indicator dashboard interval handling."""
from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from backend import crypto
from backend.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_kline() -> List[List[float]]:
    candles: List[List[float]] = []
    for i in range(300):
        base = 30000 + i
        candles.append(
            [
                float(i * 60_000),
                float(base),
                float(base + 50),
                float(base - 50),
                float(base + 10),
                float(100 + i),
                float(i * 60_000 + 59_000),
                float(1000 + i),
                int(10 + i),
                float(10 + i),
                float(20 + i),
                0,
            ]
        )
    return candles


@pytest.fixture
def patched_data_sources(monkeypatch: pytest.MonkeyPatch, sample_kline: List[List[float]]):
    async def fake_get_kline(symbol: str, interval: str):
        return sample_kline

    async def fake_fetch(endpoint: str, symbol: str, params: Dict[str, Any]):
        if "funding" in endpoint:
            return [{"fundingRate": "0.0001"} for _ in range(50)]
        if "open-interest" in endpoint:
            return [{"openInterest": str(1_000 + i)} for i in range(50)]
        return []

    monkeypatch.setattr(crypto, "get_kline", fake_get_kline)
    monkeypatch.setattr(crypto, "_fetch_bybit_data", fake_fetch)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("15m", "15m"),
        ("15", "15m"),
        (15, "15m"),
        ("60", "1h"),
        ("1h", "1h"),
        ("240m", "4h"),
        ("4h", "4h"),
        ("1440", "1d"),
        ("1d", "1d"),
    ],
)
def test_normalize_interval_variants(raw: Any, expected: str) -> None:
    assert crypto.normalize_interval(raw) == expected


@pytest.mark.parametrize("interval", ["15m", "15", "1h", "60", "4h", "240m"])
def test_indicator_dashboard_accepts_common_intervals(
    interval: str, client: TestClient, patched_data_sources
) -> None:
    response = client.get(
        "/api/crypto/indicator_dashboard",
        params={"symbol": "BTCUSDT", "interval": interval},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "indicators" in data
    assert len(data["indicators"]) > 0

