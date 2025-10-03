"""FastAPI router exposing discovery endpoints."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image

from .models import (
    DatasetTraits,
    DiscoverSession,
    ReferenceList,
    ReferenceSelectRequest,
    ReferenceStatusUpdate,
    Feature,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStatsResponse,
)
from .adapters.local import LocalAdapter
from .aggregator import aggregate_traits
from .features import build_feature
from .prompt import build_master_prompt
from .service import process_raw_items, run_discovery_sync
from .thumbs import thumbnail_path
from .store import DiscoveryStore, store


router = APIRouter(prefix="", tags=["discovery"])
prompt_router = APIRouter(prefix="/api/prompt", tags=["prompt"])
local_adapter = LocalAdapter()


class AnalyzeRequest(BaseModel):
    """Payload controlling feature analysis scope."""

    scope: Literal["selected", "all"] = "selected"


class AnalyzeResponse(BaseModel):
    """Response returned after running feature analysis."""

    started: bool
    total: int


class TraitWeights(BaseModel):
    """Optional emphasis multipliers for traits."""

    palette: Optional[float] = Field(default=None, ge=0.0)
    motifs: Optional[float] = Field(default=None, ge=0.0)
    line: Optional[float] = Field(default=None, ge=0.0)
    type: Optional[float] = Field(default=None, ge=0.0)
    comp: Optional[float] = Field(default=None, ge=0.0)


class AutofillRequest(BaseModel):
    """Payload for building a master prompt from traits."""

    session_id: str
    audience_modes: list[str] = Field(default_factory=list)
    trait_weights: TraitWeights | None = None


class AutofillResponse(BaseModel):
    """Structured master prompt output."""

    prompt_text: str
    prompt_json: dict[str, object]


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


@router.post("/{session_id}/analyze", response_model=AnalyzeResponse)
async def analyze_references(
    session_id: str,
    payload: AnalyzeRequest,
    store: DiscoveryStore = Depends(get_store),
) -> AnalyzeResponse:
    """Extract low-level features for references in the given scope."""

    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    scope = payload.scope
    if scope == "selected":
        references = store.list_references(session_id, status="selected", offset=0, limit=500)
    else:
        references = store.list_references(session_id, status=None, offset=0, limit=1000)
        references = [ref for ref in references if ref.status != "deleted"]
    if not references:
        raise HTTPException(status_code=400, detail="No references available for analysis")

    extracted: list[Feature] = []
    for reference in references:
        path = thumbnail_path(reference.id)
        if not path.exists():
            continue
        try:
            with Image.open(path) as image:
                metadata = {
                    "title": reference.title,
                    "author": reference.author,
                    "license": reference.license,
                    "url": reference.url,
                }
                feature = build_feature(reference.id, image, metadata)
        except Exception:
            continue
        extracted.append(feature)

    if extracted:
        store.upsert_features(session_id, extracted)
        if scope == "selected":
            processed_ids = {item.reference_id for item in extracted}
            selected_ids = {ref.id for ref in references}
            stale_ids = list(selected_ids - processed_ids)
            if stale_ids:
                store.delete_features(session_id, stale_ids)
    return AnalyzeResponse(started=True, total=len(extracted))


@router.get("/{session_id}/features")
async def get_session_features(
    session_id: str,
    store: DiscoveryStore = Depends(get_store),
) -> dict[str, Feature]:
    """Return extracted features keyed by reference identifier."""

    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return store.get_features(session_id)


@router.get("/{session_id}/traits", response_model=DatasetTraits)
async def get_dataset_traits(
    session_id: str,
    store: DiscoveryStore = Depends(get_store),
) -> DatasetTraits:
    """Aggregate stored features into stable dataset traits."""

    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    selected = store.list_references(session_id, status="selected", offset=0, limit=500)
    if not selected:
        raise HTTPException(status_code=400, detail="No selected references for traits")
    features = store.get_features(session_id)
    subset = {ref.id: features[ref.id] for ref in selected if ref.id in features}
    if not subset:
        raise HTTPException(status_code=404, detail="No features found for selected references")
    try:
        traits = aggregate_traits(session_id, selected, subset, weights=None, audience_modes=[])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.upsert_traits(traits)
    return traits


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


@prompt_router.post("/autofill", response_model=AutofillResponse)
async def autofill_master_prompt(
    payload: AutofillRequest,
    store: DiscoveryStore = Depends(get_store),
) -> AutofillResponse:
    """Generate a print-ready master prompt from stored traits."""

    session = store.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    traits = store.get_traits(payload.session_id)
    weights_payload = (
        payload.trait_weights.model_dump(exclude_none=True) if payload.trait_weights else None
    )

    if traits is None:
        selected = store.list_references(payload.session_id, status="selected", offset=0, limit=500)
        if not selected:
            raise HTTPException(status_code=400, detail="No selected references available")
        features = store.get_features(payload.session_id)
        subset = {ref.id: features[ref.id] for ref in selected if ref.id in features}
        if not subset:
            raise HTTPException(status_code=404, detail="Traits unavailable; run analysis first")
        traits = aggregate_traits(
            payload.session_id,
            selected,
            subset,
            weights=None,
            audience_modes=payload.audience_modes,
        )
    else:
        traits = DatasetTraits.model_validate(traits.model_dump())
        traits = traits.model_copy(update={"audience_modes": payload.audience_modes})
    store.upsert_traits(traits)
    prompt_payload = build_master_prompt(traits, payload.audience_modes, weights_payload)
    return AutofillResponse(**prompt_payload)
