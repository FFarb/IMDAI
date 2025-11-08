"""Tests for Bybit instrument specification parsing."""
from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from backend import crypto
from backend.app import app


class MockResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:  # pragma: no cover - success path only
        return None

    def json(self) -> Dict[str, Any]:
        return self._payload


class MockAsyncClient:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    async def __aenter__(self) -> "MockAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, params: Dict[str, Any] | None = None) -> MockResponse:
        return MockResponse(self._payload)


def _build_instrument_response(field: str) -> Dict[str, Any]:
    instrument: Dict[str, Any] = {
        "symbol": "BTCUSDT",
        field: "1",
        "priceFilter": {"tickSize": "0.10"},
        "lotSizeFilter": {
            "minOrderQty": "0.001",
            "qtyStep": "0.001",
            "maxOrderQty": "100",
        },
        "leverageFilter": {"minLeverage": "1", "maxLeverage": "100"},
        "feeRates": {"takerFeeRate": "0.0006", "makerFeeRate": "0.0001"},
        "riskParameters": {
            "maintainMarginRate": "0.005",
            "initialMarginRate": "0.01",
        },
        "fundingInterval": "480",
    }
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "category": "linear",
            "list": [instrument],
        },
    }


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, payload: Dict[str, Any]) -> None:
    def _factory(*args: Any, **kwargs: Any) -> MockAsyncClient:
        return MockAsyncClient(payload)

    monkeypatch.setattr(crypto.httpx, "AsyncClient", _factory)


@pytest.mark.parametrize("field", ["contractSize", "contractVal"])
def test_get_bybit_specs_handles_contract_fields(field: str, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _build_instrument_response(field)
    crypto.futures_specs_cache.clear()
    _patch_async_client(monkeypatch, payload)

    response = client.post(
        "/api/crypto/bybit/specs",
        json={"symbol": "BTCUSDT", "category": "linear"},
    )
    assert response.status_code == 200, response.json()
    data = response.json()

    assert data["symbol"] == "BTCUSDT"
    assert data["category"] == "linear"
    assert data["contract_size"] == 1.0
    assert data["tick_size"] == 0.10
    assert data["qty_step"] == 0.001
    assert data["min_order_qty"] == 0.001
    assert data["max_order_qty"] == 100.0
    assert data["leverage_min"] == 1.0
    assert data["leverage_max"] == 100.0
    # Legacy keys remain populated for backwards compatibility.
    assert data["min_qty"] == data["min_order_qty"]
    assert data["step_size"] == data["qty_step"]
    assert data["max_leverage"] == data["leverage_max"]

