from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from generate import router as generate_router
from openai_client import has_valid_key

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="IMDAI Image-Prompt App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router)


@app.get("/api/health")
def health() -> dict[str, bool]:
    """Simple readiness probe."""
    return {"ok": True, "openai_key": has_valid_key()}


__all__: List[str] = ["app"]
