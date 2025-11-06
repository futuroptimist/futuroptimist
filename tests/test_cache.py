"""Tests for the SQLite transcript cache."""

from __future__ import annotations

import time
from pathlib import Path

from tools.youtube_mcp.cache import TranscriptCache


def test_cache_roundtrip(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.sqlite3"
    cache = TranscriptCache(cache_file)
    key = cache.make_key("demo", "en")
    payload = {"value": 1}
    cache.set(key, payload, ttl_days=1)
    assert cache.get(key) == payload


def test_cache_expiry(tmp_path: Path) -> None:
    cache = TranscriptCache(tmp_path / "cache.sqlite3")
    key = cache.make_key("demo")
    cache.set(key, {"value": 1}, ttl_days=0)
    time.sleep(0.01)
    assert cache.get(key) is None
