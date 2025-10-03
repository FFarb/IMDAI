"""Persistence layer for discovery sessions and references."""
from __future__ import annotations

import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from .models import (
    DiscoverSession,
    DiscoverStats,
    Feature,
    Reference,
    DatasetTraits,
)

_DB_FILENAME = "discovery.sqlite3"
_REFERENCE_TABLE = "discovery_references"
_FEATURE_TABLE = "discovery_features"
_TRAITS_TABLE = "discovery_traits"


class DiscoveryStore:
    """SQLite backed persistence with in-memory cache for fast access."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or Path(_DB_FILENAME)
        self._lock = threading.Lock()
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Iterable[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    adapters TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stats TEXT NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_REFERENCE_TABLE} (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    site TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumb_url TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_FEATURE_TABLE} (
                    reference_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TRAITS_TABLE} (
                    session_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )

    def create_session(self, query: str, adapters: List[str]) -> DiscoverSession:
        """Create and persist a new discovery session."""
        session = DiscoverSession(
            id=str(uuid.uuid4()),
            query=query,
            adapters=adapters,
        )
        with self._lock, self._connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, query, adapters, created_at, status, stats) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session.id,
                    session.query,
                    ",".join(session.adapters),
                    session.created_at.isoformat(),
                    session.status,
                    session.stats.model_dump_json(),
                ),
            )
        return session

    def get_session(self, session_id: str) -> Optional[DiscoverSession]:
        """Fetch a session by identifier."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        stats = DiscoverStats.model_validate_json(row["stats"])
        return DiscoverSession(
            id=row["id"],
            query=row["query"],
            adapters=[item for item in row["adapters"].split(",") if item] if row["adapters"] else [],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
            stats=stats,
        )

    def upsert_references(self, references: List[Reference]) -> None:
        """Insert or update references in bulk."""
        if not references:
            return
        with self._lock, self._connection() as conn:
            conn.executemany(
                f"""
                INSERT INTO {_REFERENCE_TABLE} (id, session_id, site, url, thumb_url, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    session_id=excluded.session_id,
                    site=excluded.site,
                    url=excluded.url,
                    thumb_url=excluded.thumb_url,
                    payload=excluded.payload
                """,
                [
                    (
                        ref.id,
                        ref.session_id,
                        ref.site,
                        ref.url,
                        ref.thumb_url,
                        ref.model_dump_json(),
                    )
                    for ref in references
                ],
            )

    def list_references(
        self,
        session_id: str,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 60,
    ) -> List[Reference]:
        """List references for a session with optional status filter."""
        query = f"SELECT payload FROM {_REFERENCE_TABLE} WHERE session_id = ?"
        params: List[object] = [session_id]
        if status:
            query += " AND json_extract(payload, '$.status') = ?"
            params.append(status)
        query += " ORDER BY rowid LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Reference.model_validate_json(row["payload"]) for row in rows]

    def count_references(self, session_id: str, status: Optional[str] = None) -> int:
        """Count references for a given session."""
        query = f"SELECT COUNT(1) as cnt FROM {_REFERENCE_TABLE} WHERE session_id = ?"
        params: List[object] = [session_id]
        if status:
            query += " AND json_extract(payload, '$.status') = ?"
            params.append(status)
        with self._connection() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row["cnt"]) if row else 0

    def get_reference(self, session_id: str, reference_id: str) -> Optional[Reference]:
        """Fetch a single reference by identifier."""
        with self._connection() as conn:
            row = conn.execute(
                f"SELECT payload FROM {_REFERENCE_TABLE} WHERE id = ? AND session_id = ?",
                (reference_id, session_id),
            ).fetchone()
        if not row:
            return None
        return Reference.model_validate_json(row["payload"])

    def update_reference_status(self, session_id: str, reference_id: str, status: str) -> bool:
        """Update a reference status, returning whether anything changed."""
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                f"""
                UPDATE {_REFERENCE_TABLE} SET payload = json_set(payload, '$.status', ?)
                WHERE id = ? AND session_id = ?
                """,
                (status, reference_id, session_id),
            )
        return cursor.rowcount > 0

    def update_reference_weight(self, session_id: str, reference_id: str, weight: float) -> bool:
        """Update a reference weight."""
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                f"""
                UPDATE {_REFERENCE_TABLE} SET payload = json_set(payload, '$.weight', ?)
                WHERE id = ? AND session_id = ?
                """,
                (weight, reference_id, session_id),
            )
        return cursor.rowcount > 0

    def update_session_stats(self, session_id: str, stats: DiscoverStats) -> None:
        """Persist updated statistics for a session."""
        with self._lock, self._connection() as conn:
            conn.execute(
                "UPDATE sessions SET stats = ? WHERE id = ?",
                (stats.model_dump_json(), session_id),
            )

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update the lifecycle status of a session."""
        with self._lock, self._connection() as conn:
            conn.execute(
                "UPDATE sessions SET status = ? WHERE id = ?",
                (status, session_id),
            )

    def upsert_features(self, session_id: str, features: Sequence[Feature]) -> None:
        """Persist extracted features for a set of references."""
        if not features:
            return
        with self._lock, self._connection() as conn:
            conn.executemany(
                f"""
                INSERT INTO {_FEATURE_TABLE} (reference_id, session_id, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(reference_id) DO UPDATE SET
                    session_id=excluded.session_id,
                    payload=excluded.payload
                """,
                [
                    (
                        feature.reference_id,
                        session_id,
                        feature.model_dump_json(),
                    )
                    for feature in features
                ],
            )

    def get_feature(self, session_id: str, reference_id: str) -> Optional[Feature]:
        """Fetch features for a single reference if available."""
        with self._connection() as conn:
            row = conn.execute(
                f"SELECT payload FROM {_FEATURE_TABLE} WHERE reference_id = ? AND session_id = ?",
                (reference_id, session_id),
            ).fetchone()
        if not row:
            return None
        return Feature.model_validate_json(row["payload"])

    def get_features(self, session_id: str) -> Dict[str, Feature]:
        """Return all features for a session keyed by reference id."""
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT reference_id, payload FROM {_FEATURE_TABLE} WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        return {
            str(row["reference_id"]): Feature.model_validate_json(row["payload"])
            for row in rows
        }

    def delete_features(self, session_id: str, reference_ids: Sequence[str]) -> None:
        """Remove feature records for references no longer relevant."""
        if not reference_ids:
            return
        with self._lock, self._connection() as conn:
            conn.executemany(
                f"DELETE FROM {_FEATURE_TABLE} WHERE session_id = ? AND reference_id = ?",
                [(session_id, ref_id) for ref_id in reference_ids],
            )

    def upsert_traits(self, traits: DatasetTraits) -> None:
        """Persist aggregated dataset traits for reuse."""
        with self._lock, self._connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {_TRAITS_TABLE} (session_id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (
                    traits.session_id,
                    traits.model_dump_json(),
                    datetime.utcnow().isoformat(),
                ),
            )

    def get_traits(self, session_id: str) -> Optional[DatasetTraits]:
        """Retrieve cached dataset traits if available."""
        with self._connection() as conn:
            row = conn.execute(
                f"SELECT payload FROM {_TRAITS_TABLE} WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        return DatasetTraits.model_validate_json(row["payload"])


store = DiscoveryStore()
