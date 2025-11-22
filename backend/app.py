"""Compatibility wrapper exposing the FastAPI app from the backend package."""
from __future__ import annotations

from backend.app import app

__all__ = ["app"]
