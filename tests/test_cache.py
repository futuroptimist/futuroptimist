from __future__ import annotations

from pathlib import Path

import pytest

from tools.youtube_mcp import cache
from tools.youtube_mcp.cache import TranscriptCache


def test_cache_roundtrip(tmp_path: Path) -> None:
    store = TranscriptCache(tmp_path / "cache.sqlite3")
    payload = {"value": 42}
    store.set("key", payload, ttl_days=1)
    assert store.get("key") == payload


def test_cache_expiry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = TranscriptCache(tmp_path / "cache.sqlite3")
    monkeypatch.setattr(cache, "epoch_seconds", lambda: 0)
    store.set("key", {"value": 1}, ttl_days=1)

    # simulate expiry by advancing time beyond TTL
    monkeypatch.setattr(cache, "epoch_seconds", lambda: 10**9)
    assert store.get("key") is None
