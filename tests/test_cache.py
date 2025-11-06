from __future__ import annotations

from tools.youtube_mcp.cache import Cache


def test_cache_roundtrip(tmp_path) -> None:
    cache_path = tmp_path / "cache.sqlite3"
    cache = Cache(cache_path, ttl_days=1)
    cache.set("key", {"value": 1})
    assert cache.get("key") == {"value": 1}

    future = cache._now() + 172800
    cache._now = lambda: future  # type: ignore[assignment]
    assert cache.get("key") is None
    assert cache.purge_expired() >= 0
