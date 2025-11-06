"""Lightweight SQLite-backed cache for transcript responses."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .utils import hash_content

SCHEMA_VERSION = 1


class TranscriptCache:
    """A tiny SQLite-backed cache keyed by transcript properties."""

    def __init__(self, path: Path, schema_version: int = SCHEMA_VERSION) -> None:
        self.path = path
        self.schema_version = schema_version
        self._connection = sqlite3.connect(str(self.path))
        self._connection.row_factory = sqlite3.Row
        self._initialise()

    def _initialise(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                """
            )

    def close(self) -> None:
        self._connection.close()

    def get(self, key: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT value, expires_at, schema_version FROM entries WHERE key = ?",
            (key,),
        ).fetchone()
        if not row:
            return None
        if row["schema_version"] != self.schema_version:
            self.delete(key)
            return None
        if row["expires_at"] < time.time():
            self.delete(key)
            return None
        return json.loads(row["value"])

    def set(self, key: str, value: dict[str, Any], ttl_days: int) -> None:
        expires_at = time.time() + ttl_days * 86400
        payload = json.dumps(value, ensure_ascii=False)
        with self._connection:
            self._connection.execute(
                "REPLACE INTO entries (key, value, expires_at, schema_version) VALUES (?, ?, ?, ?)",
                (key, payload, expires_at, self.schema_version),
            )

    def delete(self, key: str) -> None:
        with self._connection:
            self._connection.execute("DELETE FROM entries WHERE key = ?", (key,))

    @staticmethod
    def make_key(*parts: str) -> str:
        """Generate a stable key from transcript parameters."""

        return hash_content("|".join(parts))


__all__ = ["SCHEMA_VERSION", "TranscriptCache"]
