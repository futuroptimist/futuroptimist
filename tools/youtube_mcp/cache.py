"""Simple sqlite-backed cache for transcript responses."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class TranscriptCache:
    """Durable cache for transcript payloads."""

    def __init__(self, cache_dir: Path, schema_version: int = 1) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.cache_dir / "cache.sqlite"
        self.schema_version = schema_version
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._initialise()

    def _initialise(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                """
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def clear_expired(self) -> None:
        now = time.time()
        with self._lock:
            with self._conn:
                self._conn.execute(
                    "DELETE FROM cache_entries WHERE expires_at <= ?", (now,)
                )

    def get(self, key: str) -> Any | None:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT value, expires_at, schema_version FROM cache_entries WHERE cache_key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            value, expires_at, schema_version = row
            if schema_version != self.schema_version:
                self.delete(key)
                return None
            if expires_at <= time.time():
                self.delete(key)
                return None
            return json.loads(value)

    def set(self, key: str, value: Any, ttl_days: int) -> None:
        expires_at = time.time() + ttl_days * 24 * 60 * 60
        payload = json.dumps(value, ensure_ascii=False)
        with self._lock:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO cache_entries (cache_key, value, expires_at, schema_version)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        value = excluded.value,
                        expires_at = excluded.expires_at,
                        schema_version = excluded.schema_version
                    """,
                    (key, payload, expires_at, self.schema_version),
                )

    def delete(self, key: str) -> None:
        with self._lock:
            with self._conn:
                self._conn.execute(
                    "DELETE FROM cache_entries WHERE cache_key = ?", (key,)
                )

    def clear(self) -> None:
        with self._lock:
            with self._conn:
                self._conn.execute("DELETE FROM cache_entries")
