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

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="IMDAI Image-Prompt App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.database.store import init_db
from backend.library import router as library_router
from backend.production import router as production_router

# Initialize DB
init_db()

app.include_router(research_router)
app.include_router(synthesize_router)
app.include_router(images_router)
app.include_router(generate_router)
app.include_router(library_router)
app.include_router(production_router)

# Mount static files
data_dir = Path(__file__).parent.parent.parent / "data" / "library"
data_dir.mkdir(parents=True, exist_ok=True)
app.mount("/library", StaticFiles(directory=data_dir), name="library")


@app.get("/api/health")
def health() -> dict[str, bool]:
    """Return service status and whether an OpenAI key is configured."""
    return {"ok": True, "openai_key": has_valid_key()}


__all__: List[str] = ["app"]
