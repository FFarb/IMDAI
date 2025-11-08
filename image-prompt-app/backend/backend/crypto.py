"""Crypto market data endpoints."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


@router.get("/kline")
async def get_kline(symbol: str = Query(..., min_length=1), interval: str = Query(..., min_length=1)) -> list[Any]:
    """Fetch candlestick (k-line) data for a symbol and interval.

    The endpoint proxies requests to the public Binance REST API and returns the
    raw JSON array of k-line entries for the requested symbol.
    """

    params = {"symbol": symbol.upper().replace("/", ""), "interval": interval}
    url = "https://api.binance.com/api/v3/klines"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network call
        logger.exception("Binance API returned an error: %s", exc)
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.RequestError as exc:  # pragma: no cover - network call
        logger.exception("Error calling Binance API: %s", exc)
        raise HTTPException(status_code=502, detail="Unable to fetch market data") from exc

    return response.json()


__all__ = ["router"]
