"""SQLite-backed cache for transcript responses."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

CACHE_SCHEMA_VERSION = 1


class Cache:
    """Durable cache persisted to sqlite."""

    def __init__(self, path: Path, ttl_days: int) -> None:
        self.path = path
        self.ttl_days = ttl_days
        self._lock = threading.Lock()
        self._initialise()

    def _initialise(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_entries_expires
                ON entries(expires_at)
                """
            )
            db.commit()

    def _now(self) -> int:
        return int(time.time())

    def get(self, key: str) -> Any | None:
        with self._lock, sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            now = self._now()
            cursor = db.execute(
                "SELECT payload, expires_at, schema_version FROM entries WHERE cache_key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            if row["schema_version"] != CACHE_SCHEMA_VERSION or row["expires_at"] <= now:
                db.execute("DELETE FROM entries WHERE cache_key = ?", (key,))
                db.commit()
                return None
            return json.loads(row["payload"])

    def set(self, key: str, value: Any) -> None:
        expires_at = self._now() + int(self.ttl_days * 86400)
        payload = json.dumps(value, sort_keys=True)
        with self._lock, sqlite3.connect(self.path) as db:
            db.execute(
                """
                INSERT INTO entries(cache_key, payload, expires_at, schema_version)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    expires_at = excluded.expires_at,
                    schema_version = excluded.schema_version
                """,
                (key, payload, expires_at, CACHE_SCHEMA_VERSION),
            )
            db.commit()

    def purge_expired(self) -> int:
        with self._lock, sqlite3.connect(self.path) as db:
            now = self._now()
            cursor = db.execute("DELETE FROM entries WHERE expires_at <= ?", (now,))
            db.commit()
            return cursor.rowcount


__all__ = ["CACHE_SCHEMA_VERSION", "Cache"]
