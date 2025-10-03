"""Discovery orchestration service."""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence

import httpx

from . import phash, quality, thumbs, watermark
from .adapters import GenericAdapter, OpenverseAdapter, UnsplashAdapter
from .models import DiscoverStats, Reference, ReferenceFlags, ReferenceScores
from .store import DiscoveryStore, store as default_store

logger = logging.getLogger(__name__)

_DISCOVERY_RPS = float(os.getenv("DISCOVERY_RPS", "3"))
_TIMEOUT = httpx.Timeout(10.0)


class RateLimiter:
    """Simple async rate limiter enforcing requests-per-second."""

    def __init__(self, rate: float) -> None:
        self.rate = rate if rate > 0 else 0
        self._lock = asyncio.Lock()
        self._last_ts = 0.0

    async def acquire(self) -> None:
        if self.rate <= 0:
            return
        min_interval = 1.0 / self.rate
        async with self._lock:
            now = time.monotonic()
            wait_for = self._last_ts + min_interval - now
            if wait_for > 0:
                await asyncio.sleep(wait_for)
                now = time.monotonic()
            self._last_ts = max(now, self._last_ts + min_interval)


def _build_adapters(names: Sequence[str]) -> Dict[str, object]:
    mapping: Dict[str, object] = {}
    for name in names:
        if name == OpenverseAdapter.name:
            mapping[name] = OpenverseAdapter()
        elif name == UnsplashAdapter.name:
            mapping[name] = UnsplashAdapter()
        elif name == GenericAdapter.name:
            mapping[name] = GenericAdapter()
    return mapping


async def process_raw_items(
    session_id: str,
    items: Sequence[Dict[str, Any]],
    limit: int,
    client: Optional[httpx.AsyncClient],
    existing: Optional[Sequence[Reference]] = None,
) -> tuple[List[Reference], int]:
    """Normalize raw adapter items into stored references."""
    processed: List[Reference] = []
    duplicates = 0
    baseline: List[Reference] = []
    if existing:
        baseline.extend(existing)
    new_count = 0
    for item in items:
        thumb_source = item.get("thumb_url")
        if not thumb_source:
            continue
        url = item.get("url")
        if not url:
            continue
        reference_id = str(item.get("id") or uuid.uuid4())
        try:
            data, mime = await thumbs.fetch_source(str(thumb_source), client)
            normalized_bytes, _, preview = thumbs.normalize_image(data, mime)
            thumb_url = thumbs.store_thumbnail(reference_id, normalized_bytes)
            p_hash_value = phash.compute_phash(preview)
            quality_score, busy_flag = quality.evaluate_quality(preview)
            watermark_flag = watermark.detect_watermark(preview)
        except Exception as exc:  # pragma: no cover - normalization failure
            logger.debug("Normalization failed for %s: %s", thumb_source, exc)
            continue

        flags = ReferenceFlags(
            watermark=watermark_flag,
            nsfw=False,
            brand_risk=False,
            busy_bg=busy_flag,
        )
        scores = ReferenceScores(
            quality=quality_score,
            risk=0.0,
            outline=0.0,
            flatness=0.0,
        )

        reference = Reference(
            id=reference_id,
            session_id=session_id,
            site=str(item.get("site", "generic")),
            url=str(url),
            thumb_url=thumb_url,
            title=item.get("title"),
            license=item.get("license"),
            author=item.get("author"),
            width=item.get("width") or preview.width,
            height=item.get("height") or preview.height,
            p_hash=p_hash_value,
            flags=flags,
            scores=scores,
        )
        duplicate_action = None
        duplicate_ref: Optional[Reference] = None
        for existing_ref in baseline:
            if not existing_ref.p_hash or not reference.p_hash:
                continue
            distance = phash.hamming_distance(existing_ref.p_hash, reference.p_hash)
            if distance <= 8:
                duplicate_ref = existing_ref
                if reference.scores.quality > existing_ref.scores.quality:
                    duplicate_action = "replace"
                else:
                    duplicate_action = "skip"
                break

        if duplicate_action == "skip":
            duplicates += 1
            continue
        if duplicate_action == "replace" and duplicate_ref is not None:
            duplicates += 1
            reference.id = duplicate_ref.id
            if duplicate_ref in baseline:
                baseline.remove(duplicate_ref)
            baseline.append(reference)
            processed.append(reference)
            continue

        if new_count >= limit:
            continue

        baseline.append(reference)
        processed.append(reference)
        new_count += 1
    return processed, duplicates


async def run_discovery(
    session_id: str,
    query: str,
    adapter_names: Sequence[str],
    limit: int,
    store: DiscoveryStore = default_store,
) -> None:
    """Execute discovery across adapters and persist references."""
    session = store.get_session(session_id)
    if not session:
        logger.warning("Attempted to run discovery for missing session %s", session_id)
        return

    store.update_session_status(session_id, "fetching")
    limiter = RateLimiter(_DISCOVERY_RPS)

    async def _rate_hook(_: httpx.Request) -> None:
        await limiter.acquire()

    adapters = _build_adapters(adapter_names)
    aggregated: List[Dict[str, Any]] = []

    existing_refs = store.list_references(session_id, status=None, offset=0, limit=1000)
    existing_refs = [ref for ref in existing_refs if ref.status != "deleted"]
    references: List[Reference] = []
    duplicate_count = 0
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, event_hooks={"request": [_rate_hook]}) as client:
            for name, adapter in adapters.items():
                try:
                    results = await adapter.search(client=client, query=query, limit=limit)  # type: ignore[attr-defined]
                except Exception as exc:  # pragma: no cover - network failures
                    logger.exception("Adapter %s failed: %s", name, exc)
                    continue
                aggregated.extend(results)
            references, duplicate_count = await process_raw_items(
                session_id,
                aggregated,
                limit,
                client,
                existing=existing_refs,
            )
    except Exception as exc:  # pragma: no cover - network failures
        logger.exception("Discovery client error: %s", exc)
        store.update_session_status(session_id, "error")
        return

    if references:
        store.upsert_references(references)

    stats: DiscoverStats = session.stats
    stats.found = len(aggregated)
    stats.unique = len(references)
    stats.dup_rate = (duplicate_count / len(aggregated)) if aggregated else 0.0
    store.update_session_stats(session_id, stats)
    store.update_session_status(session_id, "ready")


def run_discovery_sync(
    session_id: str,
    query: str,
    adapter_names: Sequence[str],
    limit: int,
    store: DiscoveryStore = default_store,
) -> None:
    """Synchronous wrapper for background execution."""
    coro = run_discovery(session_id, query, adapter_names, limit, store)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        asyncio.run(coro)
        return

    if loop.is_running():  # pragma: no cover - unlikely in background task
        loop.create_task(coro)
    else:
        loop.run_until_complete(coro)
