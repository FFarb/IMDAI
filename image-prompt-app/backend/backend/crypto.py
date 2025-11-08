"""Crypto market data endpoints."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, List, Optional

import httpx
import pandas as pd
import pandas_ta as ta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, ValidationError

from backend.bybit.models import InstrumentsResponse
from backend.bybit.parsers import (
    get_contract_size,
    pick,
    to_float,
    to_int,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])

futures_specs_cache: dict[tuple[str, str], "BybitSpecsResponse"] = {}


class BybitSymbolRequest(BaseModel):
    """Request payload for querying Bybit contract specifications."""

    symbol: str
    category: str = "linear"


class BybitSpecsResponse(BaseModel):
    """Normalized response describing Bybit instrument specifications."""

    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    category: str
    contract_size: float
    tick_size: Optional[float] = None
    qty_step: Optional[float] = None
    min_order_qty: Optional[float] = None
    max_order_qty: Optional[float] = None
    leverage_min: Optional[float] = None
    leverage_max: Optional[float] = None
    taker_fee: Optional[float] = None
    maker_fee: Optional[float] = None
    funding_interval_minutes: Optional[int] = None
    maintenance_margin_rate: Optional[float] = None
    initial_margin_rate: Optional[float] = None

    # Legacy aliases kept for backwards compatibility with earlier clients.
    min_qty: Optional[float] = None
    step_size: Optional[float] = None
    max_leverage: Optional[float] = None


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

ALLOWED_INTERVALS = {
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "12h",
    "1d",
}

MINUTE_TO_INTERVAL = {
    1: "1m",
    3: "3m",
    5: "5m",
    15: "15m",
    30: "30m",
    60: "1h",
    120: "2h",
    240: "4h",
    360: "6h",
    720: "12h",
    1440: "1d",
}


def normalize_interval(raw_interval: str | int) -> str:
    """Normalise interval strings used by Binance/Bybit endpoints."""

    if isinstance(raw_interval, int):
        minutes = raw_interval
    else:
        cleaned = raw_interval.strip().lower()
        if cleaned in ALLOWED_INTERVALS:
            return cleaned
        if cleaned.isdigit():
            minutes = int(cleaned)
        else:
            match = re.fullmatch(r"(\d+)\s*([mhd])", cleaned)
            if not match:
                raise HTTPException(status_code=422, detail=f"Unsupported interval: {raw_interval}")
            value = int(match.group(1))
            unit = match.group(2)
            if unit == "m":
                minutes = value
            elif unit == "h":
                minutes = value * 60
            else:  # unit == "d"
                minutes = value * 1440

    if minutes in MINUTE_TO_INTERVAL:
        return MINUTE_TO_INTERVAL[minutes]

    raise HTTPException(status_code=422, detail=f"Unsupported minute interval: {minutes}")


def _get_indicator_column(frame: pd.DataFrame, *candidates: str) -> pd.Series:
    """Return the first matching column from ``frame``."""

    for column in candidates:
        if column in frame:
            return frame[column]
    raise KeyError(f"None of the columns {candidates} found in frame")


@router.post("/bybit/specs")
async def get_bybit_specs(request: BybitSymbolRequest) -> BybitSpecsResponse:
    """Fetch Bybit futures contract specifications."""

    cache_key = (request.category.lower(), request.symbol.upper())
    if cache_key in futures_specs_cache:
        return futures_specs_cache[cache_key]

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(
                f"{BYBIT_V5_URL}/v5/market/instruments-info",
                params={"category": request.category, "symbol": request.symbol},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network call
        logger.exception("Bybit returned an error while fetching specs: %s", exc)
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.RequestError as exc:  # pragma: no cover - network call
        logger.exception("Network error while contacting Bybit: %s", exc)
        raise HTTPException(status_code=502, detail="Unable to fetch Bybit specifications") from exc

    data = response.json()

    try:
        parsed = InstrumentsResponse.model_validate(data)
    except ValidationError as exc:
        logger.exception("Failed to validate Bybit instruments-info payload: %s", exc)
        raise HTTPException(status_code=502, detail="Unexpected response from Bybit") from exc
    instruments = parsed.result.list if parsed.result else []
    if not instruments:
        raise HTTPException(status_code=404, detail="Symbol not found")

    instrument = instruments[0]
    instrument_dict = instrument.model_dump(exclude_unset=True, exclude_none=True)
    category = (parsed.result.category if parsed.result and parsed.result.category else request.category).lower()

    contract_size = get_contract_size(instrument_dict, category)
    tick_size = to_float(pick(instrument_dict, "priceFilter", "tickSize"))
    qty_step = to_float(pick(instrument_dict, "lotSizeFilter", "qtyStep"))
    min_order_qty = to_float(pick(instrument_dict, "lotSizeFilter", "minOrderQty"))
    max_order_qty = to_float(pick(instrument_dict, "lotSizeFilter", "maxOrderQty"))
    leverage_min = to_float(pick(instrument_dict, "leverageFilter", "minLeverage"))
    leverage_max = to_float(pick(instrument_dict, "leverageFilter", "maxLeverage"))
    maintenance_margin_rate = to_float(pick(instrument_dict, "riskParameters", "maintainMarginRate"))
    initial_margin_rate = to_float(pick(instrument_dict, "riskParameters", "initialMarginRate"))
    taker_fee = to_float(pick(instrument_dict, "feeRates", "takerFeeRate"))
    maker_fee = to_float(pick(instrument_dict, "feeRates", "makerFeeRate"))
    funding_interval_minutes = to_int(pick(instrument_dict, "fundingInterval"))

    response_payload = BybitSpecsResponse(
        symbol=instrument.symbol or request.symbol.upper(),
        category=category,
        contract_size=contract_size,
        tick_size=tick_size,
        qty_step=qty_step,
        min_order_qty=min_order_qty,
        max_order_qty=max_order_qty,
        leverage_min=leverage_min,
        leverage_max=leverage_max,
        taker_fee=taker_fee,
        maker_fee=maker_fee,
        funding_interval_minutes=funding_interval_minutes,
        maintenance_margin_rate=maintenance_margin_rate,
        initial_margin_rate=initial_margin_rate,
        min_qty=min_order_qty,
        step_size=qty_step,
        max_leverage=leverage_max,
    )

    futures_specs_cache[cache_key] = response_payload
    return response_payload


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


class IndicatorSignal(BaseModel):
    name: str
    params: str
    signal: str
    streak: int


class IndicatorDashboardResponse(BaseModel):
    indicators: List[IndicatorSignal]


async def _fetch_bybit_data(endpoint: str, symbol: str, params: dict[str, Any]) -> list[Any]:
    """Helper to fetch data from Bybit v5 API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BYBIT_V5_URL}{endpoint}",
                params={"category": "linear", "symbol": symbol, **params},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("result", {}).get("list", [])
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(f"Failed to fetch {endpoint} for {symbol}: {e}")
            return []


@router.get("/indicator_dashboard", response_model=IndicatorDashboardResponse)
async def get_indicator_dashboard(
    symbol: str = Query("BTCUSDT"), interval: str = Query("15m")
) -> IndicatorDashboardResponse:
    """Fetch and compute a dashboard of technical indicators."""
    normalized_interval = normalize_interval(interval)

    # Fetch all required data in parallel
    kline_data, funding_rate_data, open_interest_data = await asyncio.gather(
        get_kline(symbol=symbol, interval=normalized_interval),
        _fetch_bybit_data("/v5/market/funding/history", symbol, {"limit": 200}),
        _fetch_bybit_data(
            "/v5/market/open-interest",
            symbol,
            {"intervalTime": normalized_interval, "limit": 200},
        ),
    )

    if not kline_data:
        raise HTTPException(status_code=404, detail="No k-line data available")

    df = pd.DataFrame(
        kline_data,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )
    df = df.astype(
        {
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )

    indicators = []

    def get_signal_and_streak(series: pd.Series) -> tuple[str, int]:
        if series.empty:
            return "NEUTRAL", 0
        if series.iloc[-1] > 0:
            signal = "LONG"
        elif series.iloc[-1] < 0:
            signal = "SHORT"
        else:
            signal = "NEUTRAL"

        streak = 0
        for i in range(len(series) - 1, -1, -1):
            if (series.iloc[i] > 0 and signal == "LONG") or \
               (series.iloc[i] < 0 and signal == "SHORT") or \
               (series.iloc[i] == 0 and signal == "NEUTRAL"):
                streak += 1
            else:
                break
        return signal, streak

    # 1. Trend
    ema_21 = ta.ema(df["close"], length=21)
    ema_55 = ta.ema(df["close"], length=55)
    ema_signal = pd.Series(ema_21 > ema_55).astype(int) - pd.Series(ema_21 < ema_55).astype(int)
    signal, streak = get_signal_and_streak(ema_signal)
    indicators.append(IndicatorSignal(name="EMA", params="21, 55", signal=signal, streak=streak))

    sma_50 = ta.sma(df["close"], length=50)
    sma_100 = ta.sma(df["close"], length=100)
    sma_signal = pd.Series(sma_50 > sma_100).astype(int) - pd.Series(sma_50 < sma_100).astype(int)
    signal, streak = get_signal_and_streak(sma_signal)
    indicators.append(IndicatorSignal(name="SMA", params="50, 100", signal=signal, streak=streak))

    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    macd_signal = pd.Series(macd['MACD_12_26_9'] > macd['MACDs_12_26_9']).astype(int) - pd.Series(macd['MACD_12_26_9'] < macd['MACDs_12_26_9']).astype(int)
    signal, streak = get_signal_and_streak(macd_signal)
    indicators.append(IndicatorSignal(name="MACD", params="12, 26, 9", signal=signal, streak=streak))

    adx = ta.adx(df["high"], df["low"], df["close"], length=14)
    adx_long = (adx['ADX_14'] > 25) & (adx['DMP_14'] > adx['DMN_14'])
    adx_short = (adx['ADX_14'] > 25) & (adx['DMN_14'] > adx['DMP_14'])
    adx_signal = adx_long.astype(int) - adx_short.astype(int)
    signal, streak = get_signal_and_streak(adx_signal)
    indicators.append(IndicatorSignal(name="ADX", params="14", signal=signal, streak=streak))

    supertrend = ta.supertrend(df["high"], df["low"], df["close"], length=14, multiplier=3)
    supertrend_line = _get_indicator_column(supertrend, "SUPERT_14_3.0", "SUPERT_14_3")
    st_signal = pd.Series(df["close"] > supertrend_line).astype(int) - pd.Series(df["close"] < supertrend_line).astype(int)
    signal, streak = get_signal_and_streak(st_signal)
    indicators.append(IndicatorSignal(name="SuperTrend", params="14, 3", signal=signal, streak=streak))

    ichimoku = ta.ichimoku(
        df["high"],
        df["low"],
        df["close"],
        tenkan=9,
        kijun=26,
        senkou=52,
        ichimoku_spans=True,
        ichimoku_kc=True,
    )
    ichimoku_cloud = ichimoku[0]
    isa = _get_indicator_column(ichimoku_cloud, "ISA_9_26_52", "ISA_9")
    isb = _get_indicator_column(ichimoku_cloud, "ISB_9_26_52", "ISB_26")
    price_gt_kumo = (df["close"] > isa) & (df["close"] > isb)
    price_lt_kumo = (df["close"] < isa) & (df["close"] < isb)
    tenkan_gt_kijun = ichimoku_cloud["ITS_9"] > ichimoku_cloud["IKS_26"]
    ichimoku_long = price_gt_kumo & tenkan_gt_kijun
    ichimoku_short = price_lt_kumo & ~tenkan_gt_kijun
    ichimoku_signal = ichimoku_long.astype(int) - ichimoku_short.astype(int)
    signal, streak = get_signal_and_streak(ichimoku_signal)
    indicators.append(IndicatorSignal(name="Ichimoku", params="9, 26, 52, 26", signal=signal, streak=streak))

    # 2. Momentum
    rsi = ta.rsi(df["close"], length=14)
    rsi_long = rsi < 30
    rsi_short = rsi > 70
    rsi_signal = rsi_long.astype(int) - rsi_short.astype(int)
    signal, streak = get_signal_and_streak(rsi_signal)
    indicators.append(IndicatorSignal(name="RSI", params="14", signal=signal, streak=streak))

    stoch = ta.stoch(df["high"], df["low"], df["close"], k=14, d=3, smooth_k=3)
    stoch_long = stoch['STOCHk_14_3_3'] < 20
    stoch_short = stoch['STOCHk_14_3_3'] > 80
    stoch_signal = stoch_long.astype(int) - stoch_short.astype(int)
    signal, streak = get_signal_and_streak(stoch_signal)
    indicators.append(IndicatorSignal(name="Stochastic", params="14, 3, 3", signal=signal, streak=streak))

    cci = ta.cci(df["high"], df["low"], df["close"], length=20)
    cci_long = cci < -100
    cci_short = cci > 100
    cci_signal = cci_long.astype(int) - cci_short.astype(int)
    signal, streak = get_signal_and_streak(cci_signal)
    indicators.append(IndicatorSignal(name="CCI", params="20", signal=signal, streak=streak))

    mom = ta.mom(df["close"], length=10)
    mom_signal = pd.Series(mom > 0).astype(int) - pd.Series(mom < 0).astype(int)
    signal, streak = get_signal_and_streak(mom_signal)
    indicators.append(IndicatorSignal(name="Momentum", params="10", signal=signal, streak=streak))

    willr = ta.willr(df["high"], df["low"], df["close"], length=14)
    willr_long = willr < -80
    willr_short = willr > -20
    willr_signal = willr_long.astype(int) - willr_short.astype(int)
    signal, streak = get_signal_and_streak(willr_signal)
    indicators.append(IndicatorSignal(name="Williams %R", params="14", signal=signal, streak=streak))

    # 3. Volatility
    atr = ta.atr(df["high"], df["low"], df["close"], length=14)
    atr_ma = ta.sma(atr, length=14)
    atr_signal = pd.Series(atr > atr_ma).astype(int) - pd.Series(atr < atr_ma).astype(int)
    signal, streak = get_signal_and_streak(atr_signal)
    indicators.append(IndicatorSignal(name="ATR", params="14", signal=signal, streak=streak))

    bbands = ta.bbands(df["close"], length=20, std=2)
    bb_lower = _get_indicator_column(
        bbands,
        "BBL_20_2.0",
        "BBL_20_2",
        "BBL_20_2.0_2.0",
    )
    bb_upper = _get_indicator_column(
        bbands,
        "BBU_20_2.0",
        "BBU_20_2",
        "BBU_20_2.0_2.0",
    )
    bb_long = df["close"] < bb_lower
    bb_short = df["close"] > bb_upper
    bb_signal = bb_long.astype(int) - bb_short.astype(int)
    signal, streak = get_signal_and_streak(bb_signal)
    indicators.append(IndicatorSignal(name="Bollinger Bands", params="20, 2", signal=signal, streak=streak))

    donchian = ta.donchian(df["high"], df["low"], lower_length=20, upper_length=20)
    donchian_long = df["close"] == donchian['DCU_20_20']
    donchian_short = df["close"] == donchian['DCL_20_20']
    donchian_signal = donchian_long.astype(int) - donchian_short.astype(int)
    signal, streak = get_signal_and_streak(donchian_signal)
    indicators.append(IndicatorSignal(name="Donchian Channel", params="20", signal=signal, streak=streak))

    kc = ta.kc(df["high"], df["low"], df["close"], length=20, scalar=1.5)
    kc_long = df["close"] > kc['KCUe_20_1.5']
    kc_short = df["close"] < kc['KCLe_20_1.5']
    kc_signal = kc_long.astype(int) - kc_short.astype(int)
    signal, streak = get_signal_and_streak(kc_signal)
    indicators.append(IndicatorSignal(name="Keltner Channel", params="20, 1.5", signal=signal, streak=streak))

    # 4. Volume / Microstructure
    vol_ma = ta.sma(df["volume"], length=20)
    vol_signal = pd.Series(df["volume"] > vol_ma).astype(int) - pd.Series(df["volume"] < vol_ma).astype(int)
    signal, streak = get_signal_and_streak(vol_signal)
    indicators.append(IndicatorSignal(name="Volume MA", params="20", signal=signal, streak=streak))

    obv = ta.obv(df["close"], df["volume"])
    obv_ma = ta.sma(obv, length=20)
    obv_signal = pd.Series(obv > obv_ma).astype(int) - pd.Series(obv < obv_ma).astype(int)
    signal, streak = get_signal_and_streak(obv_signal)
    indicators.append(IndicatorSignal(name="OBV", params="20", signal=signal, streak=streak))

    vwap = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
    vwap_signal = pd.Series(df["close"] > vwap).astype(int) - pd.Series(df["close"] < vwap).astype(int)
    signal, streak = get_signal_and_streak(vwap_signal)
    indicators.append(IndicatorSignal(name="VWAP", params="Session", signal=signal, streak=streak))

    # NOTE: The following indicators require access to order book depth,
    #       CVD, or other specialized data not available from the basic k-line endpoint.
    # indicators.append(IndicatorSignal(name="Orderbook Imbalance", params="5", signal="NEUTRAL", streak=0))
    # indicators.append(IndicatorSignal(name="CVD", params="10", signal="NEUTRAL", streak=0))

    # 5. Derivatives Metrics
    if funding_rate_data:
        fr_df = pd.DataFrame(funding_rate_data).astype({"fundingRate": "float64"})
        fr_ma = ta.sma(fr_df["fundingRate"], length=7)
        fr_signal = pd.Series(fr_df["fundingRate"] > fr_ma).astype(int) - pd.Series(fr_df["fundingRate"] < fr_ma).astype(int)
        signal, streak = get_signal_and_streak(fr_signal)
    else:
        signal, streak = "NEUTRAL", 0
    indicators.append(IndicatorSignal(name="Funding Rate", params="7-avg", signal=signal, streak=streak))

    if open_interest_data:
        oi_df = pd.DataFrame(open_interest_data).astype({"openInterest": "float64"})
        oi_delta = oi_df["openInterest"].diff(periods=15)
        oi_signal = pd.Series(oi_delta > 0).astype(int) - pd.Series(oi_delta < 0).astype(int)
        signal, streak = get_signal_and_streak(oi_signal)
    else:
        signal, streak = "NEUTRAL", 0
    indicators.append(IndicatorSignal(name="Open Interest", params="15-bar Δ", signal=signal, streak=streak))

    # NOTE: The following indicators require access to spot market prices or liquidation feeds.
    # indicators.append(IndicatorSignal(name="Basis Spread", params="Spot-Futures", signal="NEUTRAL", streak=0))
    # indicators.append(IndicatorSignal(name="Liquidation Density", params="5-bar", signal="NEUTRAL", streak=0))

    # 6. Composite
    trend_mom_long = (ema_signal.iloc[-1] > 0) and (rsi.iloc[-1] < 30)
    trend_mom_short = (ema_signal.iloc[-1] < 0) and (rsi.iloc[-1] > 70)
    trend_mom_signal_val = 1 if trend_mom_long else -1 if trend_mom_short else 0
    indicators.append(IndicatorSignal(name="Trend+Momentum", params="EMA+RSI", signal="LONG" if trend_mom_long else "SHORT" if trend_mom_short else "NEUTRAL", streak=1 if trend_mom_signal_val !=0 else 0))

    atr = ta.atr(df["high"], df["low"], df["close"], length=14)
    atr_ma = ta.sma(atr, length=14)
    vol_exp = atr.iloc[-1] > atr_ma.iloc[-1] if not atr.empty and not atr_ma.empty else False
    indicators.append(IndicatorSignal(name="Volatility Expansion", params="ATR↑", signal="NEUTRAL" if vol_exp else "NEUTRAL", streak=0))

    vol_conf_long = (ema_signal.iloc[-1] > 0) and (df["volume"].iloc[-1] > vol_ma.iloc[-1] * 1.2) if not ema_signal.empty and not vol_ma.empty else False
    vol_conf_short = (ema_signal.iloc[-1] < 0) and (df["volume"].iloc[-1] > vol_ma.iloc[-1] * 1.2) if not ema_signal.empty and not vol_ma.empty else False
    vol_conf_signal_val = 1 if vol_conf_long else -1 if vol_conf_short else 0
    indicators.append(IndicatorSignal(name="Volume Confirmation", params="vol/avg>1.2", signal="LONG" if vol_conf_long else "SHORT" if vol_conf_short else "NEUTRAL", streak=1 if vol_conf_signal_val != 0 else 0))

    indicators.append(IndicatorSignal(name="Funding Alignment", params="Fund+EMA", signal="NEUTRAL", streak=0))

    return IndicatorDashboardResponse(indicators=indicators)


__all__ = ["router"]
