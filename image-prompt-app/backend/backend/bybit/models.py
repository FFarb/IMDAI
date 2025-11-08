"""Typed models representing Bybit instrument responses."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PriceFilter(BaseModel):
    tickSize: Optional[str] = None


class LotSizeFilter(BaseModel):
    maxOrderQty: Optional[str] = None
    minOrderQty: Optional[str] = None
    qtyStep: Optional[str] = None


class LeverageFilter(BaseModel):
    minLeverage: Optional[str] = None
    maxLeverage: Optional[str] = None
    leverageStep: Optional[str] = None


class FeeRates(BaseModel):
    takerFeeRate: Optional[str] = None
    makerFeeRate: Optional[str] = None


class RiskParameters(BaseModel):
    maintainMarginRate: Optional[str] = None
    initialMarginRate: Optional[str] = None


class BybitInstrument(BaseModel):
    symbol: Optional[str] = None
    contractSize: Optional[str] = None
    contractVal: Optional[str] = None
    priceFilter: Optional[PriceFilter] = None
    lotSizeFilter: Optional[LotSizeFilter] = None
    leverageFilter: Optional[LeverageFilter] = None
    feeRates: Optional[FeeRates] = None
    riskParameters: Optional[RiskParameters] = None
    fundingInterval: Optional[str] = None


class InstrumentsResult(BaseModel):
    category: Optional[str] = None
    list: List[BybitInstrument] = Field(default_factory=list)


class InstrumentsResponse(BaseModel):
    retCode: int
    retMsg: Optional[str] = None
    result: Optional[InstrumentsResult] = None
