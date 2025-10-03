"""Pydantic models for the discovery subsystem."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DiscoverStats(BaseModel):
    """Aggregated metrics for a discovery session."""

    found: int = 0
    unique: int = 0
    selected: int = 0
    dup_rate: float = 0.0


class DiscoverSession(BaseModel):
    """Represents a discovery session lifecycle."""

    id: str
    query: str
    adapters: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["idle", "fetching", "ready", "error"] = "idle"
    stats: DiscoverStats = Field(default_factory=DiscoverStats)


class ReferenceFlags(BaseModel):
    """Binary flags describing potential risks."""

    watermark: bool = False
    nsfw: bool = False
    brand_risk: bool = False
    busy_bg: bool = False


class ReferenceScores(BaseModel):
    """Numerical scores derived from analysis."""

    quality: float = 0.0
    risk: float = 0.0
    outline: float = 0.0
    flatness: float = 0.0


class Reference(BaseModel):
    """Reference asset returned by discovery adapters."""

    id: str
    session_id: str
    site: Literal["openverse", "unsplash", "generic", "local"]
    url: str
    thumb_url: str
    title: Optional[str] = None
    license: Optional[str] = None
    author: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    p_hash: Optional[str] = None
    flags: ReferenceFlags = Field(default_factory=ReferenceFlags)
    scores: ReferenceScores = Field(default_factory=ReferenceScores)
    status: Literal["result", "selected", "hidden", "deleted"] = "result"
    weight: float = 1.0


class ReferenceList(BaseModel):
    """Container for returning references."""

    items: List[Reference]
    total: int


class SessionCreateRequest(BaseModel):
    """Request payload for initiating discovery."""

    query: str
    adapters: List[str] = Field(default_factory=lambda: ["openverse", "unsplash", "generic"])
    limit: int = 60


class SessionCreateResponse(BaseModel):
    """Response payload for discovery creation."""

    session_id: str


class ReferenceStatusUpdate(BaseModel):
    """Payload used for status updates."""

    reference_id: str


class ReferenceSelectRequest(ReferenceStatusUpdate):
    """Request for selecting a reference with optional weight."""

    weight: Optional[float] = None


class SessionStatsResponse(BaseModel):
    """Response wrapping session statistics."""

    stats: DiscoverStats


FiltersType = Dict[str, str | List[str] | int | None]
