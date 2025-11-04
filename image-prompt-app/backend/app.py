from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research import router as research_router
from synthesize import router as synthesize_router
from images import router as images_router
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

# Include the new modular routers
app.include_router(research_router)
app.include_router(synthesize_router)
app.include_router(images_router)

# The generate router can be kept as a legacy full-pipeline endpoint or removed.
# For this refactor, we'll keep it as an optional orchestrator.
app.include_router(generate_router)


@app.get("/api/health")
def health() -> dict[str, bool]:
    """Simple readiness probe."""
    return {"ok": True, "openai_key": has_valid_key()}


__all__: List[str] = ["app"]
