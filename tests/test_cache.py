from pathlib import Path

from tools.youtube_mcp.cache import TranscriptCache


def test_cache_roundtrip(tmp_path: Path):
    cache = TranscriptCache(tmp_path)
    cache.set("key", {"value": 1}, ttl_days=1)
    assert cache.get("key") == {"value": 1}


def test_cache_expiry(tmp_path: Path):
    cache = TranscriptCache(tmp_path)
    cache.set("expiring", {"value": 2}, ttl_days=-1)
    assert cache.get("expiring") is None


def test_cache_schema_version(tmp_path: Path):
    cache = TranscriptCache(tmp_path, schema_version=2)
    cache.set("schema", {"value": 3}, ttl_days=1)
    cache.schema_version = 1
    assert cache.get("schema") is None


def test_cache_delete_and_clear(tmp_path: Path):
    cache = TranscriptCache(tmp_path)
    cache.set("a", {"value": 1}, ttl_days=1)
    cache.set("b", {"value": 2}, ttl_days=1)
    cache.delete("a")
    assert cache.get("a") is None
    cache.clear()
    assert cache.get("b") is None


def test_cache_clear_expired(tmp_path: Path):
    cache = TranscriptCache(tmp_path)
    cache.set("will_expire", {"value": 1}, ttl_days=-1)
    cache.clear_expired()
    assert cache.get("will_expire") is None
