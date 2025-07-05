import json


import scripts.gh_rest as gh


class Resp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_fetch_commit_stats_uses_cache(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({"o/r@sha": {"additions": 1, "deletions": 2}}))
    monkeypatch.setattr(gh, "CACHE_FILE", cache)
    monkeypatch.setenv("GH_TOKEN", "x")
    called = []
    monkeypatch.setattr(gh.requests, "get", lambda *a, **k: called.append(1))

    stats = gh.fetch_commit_stats("o", "r", "sha")
    assert stats == {"additions": 1, "deletions": 2}
    assert not called


def test_fetch_commit_stats_fetches_and_saves(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(gh, "CACHE_FILE", cache)
    monkeypatch.setenv("GH_TOKEN", "x")

    def fake_get(url, headers, timeout):
        return Resp({"stats": {"additions": 3, "deletions": 4}})

    monkeypatch.setattr(gh.requests, "get", fake_get)

    stats = gh.fetch_commit_stats("o", "r", "sha2")
    assert stats == {"additions": 3, "deletions": 4}
    data = json.loads(cache.read_text())
    assert data["o/r@sha2"] == stats
