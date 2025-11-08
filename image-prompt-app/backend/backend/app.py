"""FastAPI application entrypoint for the IMDAI backend."""
from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.openai_client import has_valid_key
from backend.generate import router as generate_router
from backend.images import router as images_router
from backend.research import router as research_router
from backend.synthesize import router as synthesize_router
from backend.crypto import router as crypto_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="IMDAI Image-Prompt App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)
app.include_router(synthesize_router)
app.include_router(images_router)
app.include_router(generate_router)
app.include_router(crypto_router)


@app.get("/api/health")
def health() -> dict[str, bool]:
    """Return service status and whether an OpenAI key is configured."""
    return {"ok": True, "openai_key": has_valid_key()}


__all__: List[str] = ["app"]
