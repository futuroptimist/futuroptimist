"""SQLite-backed cache for transcript responses."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .utils import epoch_seconds

SCHEMA_VERSION = 1


class TranscriptCache:
    """Durable cache that stores serialized transcript responses."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transcripts (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                """
            )

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Return cached data if present and not expired."""

        row = self._conn.execute(
            "SELECT payload, expires_at, schema_version FROM transcripts WHERE cache_key=?",
            (key,),
        ).fetchone()
        if not row:
            return None
        payload, expires_at, schema_version = row
        if schema_version != SCHEMA_VERSION:
            self.delete(key)
            return None
        if expires_at <= epoch_seconds():
            self.delete(key)
            return None
        return json.loads(payload)

    def set(self, key: str, value: dict[str, Any], ttl_days: int) -> None:
        """Store cached data with a TTL expressed in days."""

        expires_at = epoch_seconds() + ttl_days * 86400
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
        with self._conn:
            self._conn.execute(
                "REPLACE INTO transcripts(cache_key, payload, expires_at, schema_version) VALUES (?, ?, ?, ?)",
                (key, payload, expires_at, SCHEMA_VERSION),
            )

    def delete(self, key: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM transcripts WHERE cache_key=?", (key,))

    def close(self) -> None:
        self._conn.close()
