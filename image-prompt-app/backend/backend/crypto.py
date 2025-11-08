"""Crypto market data endpoints."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])

futures_specs_cache: dict[str, Any] = {}


class BybitSymbolRequest(BaseModel):
    symbol: str


class BybitSpecsResponse(BaseModel):
    contract_size: float
    tick_size: float
    min_qty: float
    step_size: float
    max_leverage: float
    maintenance_margin_rate: float
    initial_margin_rate: float
    taker_fee: float
    maker_fee: float
    funding_interval_minutes: int


class LiqPriceRequest(BaseModel):
    side: str
    entry_price: float
    qty: float
    leverage: int
    mmr: float
    contract_value: float


class PnlRequest(BaseModel):
    entry_px: float
    exit_px: float
    qty: float
    side: str
    contract_value: float
    taker_fee: float


class FundingPnlRequest(BaseModel):
    notional: float
    funding_rate: float
    time_delta_hours: float
    funding_interval_hours: float
    side: str


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


BYBIT_V5_URL = "https://api.bybit.com"


@router.post("/bybit/specs")
async def get_bybit_specs(request: BybitSymbolRequest) -> BybitSpecsResponse:
    """Fetch Bybit futures contract specifications."""
    if request.symbol in futures_specs_cache:
        return futures_specs_cache[request.symbol]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BYBIT_V5_URL}/v5/market/instruments-info",
            params={"category": "linear", "symbol": request.symbol},
        )
        response.raise_for_status()
        data = response.json()

    specs = data["result"]["list"][0]
    result = BybitSpecsResponse(
        contract_size=float(specs["contractVal"]),
        tick_size=float(specs["priceFilter"]["tickSize"]),
        min_qty=float(specs["lotSizeFilter"]["minOrderQty"]),
        step_size=float(specs["lotSizeFilter"]["qtyStep"]),
        max_leverage=float(specs["leverageFilter"]["maxLeverage"]),
        maintenance_margin_rate=float(specs["riskParameters"]["maintainMarginRate"]),
        initial_margin_rate=float(specs["riskParameters"]["initialMarginRate"]),
        taker_fee=float(specs["feeRates"]["takerFeeRate"]),
        maker_fee=float(specs["feeRates"]["makerFeeRate"]),
        funding_interval_minutes=int(specs["fundingInterval"]),
    )
    futures_specs_cache[request.symbol] = result
    return result


@router.get("/bybit/market_price")
async def get_bybit_market_price(symbol: str) -> dict[str, float]:
    """Fetch Bybit market prices."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BYBIT_V5_URL}/v5/market/tickers",
            params={"category": "linear", "symbol": symbol},
        )
        response.raise_for_status()
        data = response.json()

    ticker = data["result"]["list"][0]
    return {
        "index_price": float(ticker["indexPrice"]),
        "mark_price": float(ticker["markPrice"]),
    }


def _estimate_liq_price(
    side: str, entry_price: float, qty: float, leverage: int, mmr: float, contract_value: float
) -> float:
    """Estimate liquidation price."""
    if side.lower() == "long":
        liq_price = (entry_price * qty * contract_value * (1 / leverage - 1)) / (
            qty * contract_value * (mmr - 1)
        )
    else:
        liq_price = (entry_price * qty * contract_value * (1 / leverage + 1)) / (
            qty * contract_value * (mmr + 1)
        )
    return liq_price


@router.post("/bybit/estimate_liq_price")
async def estimate_liq_price(request: LiqPriceRequest) -> dict[str, float]:
    """Estimate liquidation price."""
    liq_price = _estimate_liq_price(
        request.side,
        request.entry_price,
        request.qty,
        request.leverage,
        request.mmr,
        request.contract_value,
    )
    return {"liquidation_price": liq_price}


@router.post("/bybit/calculate_pnl")
async def calculate_pnl(request: PnlRequest) -> dict[str, float]:
    """Calculate PnL."""
    if request.side.lower() == "long":
        gross_pnl = (request.exit_px - request.entry_px) * request.qty * request.contract_value
    else:
        gross_pnl = (request.entry_px - request.exit_px) * request.qty * request.contract_value

    entry_fee = request.entry_px * request.qty * request.contract_value * request.taker_fee
    exit_fee = request.exit_px * request.qty * request.contract_value * request.taker_fee
    net_pnl = gross_pnl - entry_fee - exit_fee
    return {"realized_pnl": net_pnl}


@router.get("/bybit/funding_rate")
async def get_bybit_funding_rate(symbol: str) -> dict[str, float]:
    """Fetch Bybit funding rate."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BYBIT_V5_URL}/v5/market/tickers",
            params={"category": "linear", "symbol": symbol},
        )
        response.raise_for_status()
        data = response.json()

    ticker = data["result"]["list"][0]
    return {"funding_rate": float(ticker["fundingRate"])}


@router.post("/bybit/calculate_funding_pnl")
async def calculate_funding_pnl(request: FundingPnlRequest) -> dict[str, float]:
    """Calculate funding PnL."""
    side_sign = -1 if request.side.lower() == "long" else 1
    periods = request.time_delta_hours / request.funding_interval_hours
    funding_pnl = request.notional * request.funding_rate * periods * side_sign
    return {"funding_pnl": funding_pnl}


__all__ = ["router"]
