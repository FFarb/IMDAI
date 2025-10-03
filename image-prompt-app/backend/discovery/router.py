"""FastAPI router exposing discovery endpoints."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from .models import (
    DiscoverSession,
    ReferenceList,
    ReferenceSelectRequest,
    ReferenceStatusUpdate,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatsResponse,
)
from .adapters.local import LocalAdapter
from .service import process_raw_items, run_discovery_sync
from .thumbs import thumbnail_path
from .store import DiscoveryStore, store


router = APIRouter(prefix="", tags=["discovery"])
local_adapter = LocalAdapter()


def get_store() -> DiscoveryStore:
    """Dependency injector for the discovery store."""
    return store


def _trigger_discovery(
    background_tasks: BackgroundTasks,
    session: DiscoverSession,
    limit: int,
) -> None:
    """Schedule the discovery pipeline to run in the background."""

    background_tasks.add_task(
        run_discovery_sync,
        session.id,
        session.query,
        session.adapters,
        limit,
    )


@router.post("/search", response_model=SessionCreateResponse)
async def create_discovery_session(
    payload: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    store: DiscoveryStore = Depends(get_store),
) -> SessionCreateResponse:
    """Create a new discovery session and enqueue discovery work."""
    session = store.create_session(query=payload.query, adapters=payload.adapters)
    store.update_session_status(session.id, "fetching")
    _trigger_discovery(background_tasks, session, payload.limit)
    return SessionCreateResponse(session_id=session.id)


@router.get("/{session_id}/items", response_model=ReferenceList)
async def list_discovery_items(
    session_id: str,
    status: str | None = Query(default=None, pattern="^(result|selected|hidden|deleted)$"),
    offset: int = 0,
    limit: int = Query(default=60, le=200),
    store: DiscoveryStore = Depends(get_store),
) -> ReferenceList:
    """Return references for a discovery session."""
    items = store.list_references(session_id=session_id, status=status, offset=offset, limit=limit)
    total = store.count_references(session_id=session_id, status=status)
    return ReferenceList(items=items, total=total)


@router.post("/{session_id}/select")
async def select_reference(
    session_id: str,
    payload: ReferenceSelectRequest,
    store: DiscoveryStore = Depends(get_store),
) -> dict[str, str]:
    """Mark a reference as selected optionally updating weight."""
    updated = store.update_reference_status(session_id, payload.reference_id, "selected")
    if not updated:
        raise HTTPException(status_code=404, detail="Reference not found")
    if payload.weight is not None:
        store.update_reference_weight(session_id, payload.reference_id, payload.weight)
    return {"status": "ok"}


@router.post("/{session_id}/hide")
async def hide_reference(
    session_id: str,
    payload: ReferenceStatusUpdate,
    store: DiscoveryStore = Depends(get_store),
) -> dict[str, str]:
    """Hide a reference from results."""
    updated = store.update_reference_status(session_id, payload.reference_id, "hidden")
    if not updated:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"status": "ok"}


@router.post("/{session_id}/delete")
async def delete_reference(
    session_id: str,
    payload: ReferenceStatusUpdate,
    store: DiscoveryStore = Depends(get_store),
) -> dict[str, str]:
    """Soft delete a reference."""
    updated = store.update_reference_status(session_id, payload.reference_id, "deleted")
    if not updated:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"status": "ok"}


@router.post("/{session_id}/star")
async def star_reference(
    session_id: str,
    payload: ReferenceStatusUpdate,
    store: DiscoveryStore = Depends(get_store),
) -> dict[str, float]:
    """Cycle through reference weights."""
    target = store.get_reference(session_id, payload.reference_id)
    if not target:
        raise HTTPException(status_code=404, detail="Reference not found")
    next_weight = 1.5 if target.weight == 1.0 else 2.0 if target.weight == 1.5 else 1.0
    store.update_reference_weight(session_id, payload.reference_id, next_weight)
    return {"weight": next_weight}


@router.post("/{session_id}/local")
async def upload_local_references(
    session_id: str,
    files: list[UploadFile] = File(...),
    store: DiscoveryStore = Depends(get_store),
) -> dict[str, int]:
    """Ingest locally uploaded reference files."""
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        raw_items = await local_adapter.ingest(session_id, files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not raw_items:
        return {"count": 0}
    existing_refs = store.list_references(session_id, status=None, offset=0, limit=1000)
    existing_refs = [ref for ref in existing_refs if ref.status != "deleted"]
    references, duplicate_count = await process_raw_items(
        session_id,
        raw_items,
        len(raw_items),
        client=None,
        existing=existing_refs,
    )
    if not references:
        return {"count": 0}
    store.upsert_references(references)
    stats = session.stats
    stats.found = len(raw_items)
    stats.unique = len(references)
    stats.dup_rate = (duplicate_count / len(raw_items)) if raw_items else 0.0
    store.update_session_stats(session_id, stats)
    return {"count": len(references)}


@router.get("/{session_id}/stats", response_model=SessionStatsResponse)
async def discovery_stats(
    session_id: str,
    store: DiscoveryStore = Depends(get_store),
) -> SessionStatsResponse:
    """Return statistics for a session."""
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionStatsResponse(stats=session.stats)


@router.get("/thumb/{reference_id}")
async def get_thumbnail(reference_id: str) -> FileResponse:
    """Serve normalized thumbnails via proxy endpoint."""
    path = thumbnail_path(reference_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(path, media_type="image/webp")
