import pytest
from src import gh_graphql, generate_heatmap


class Resp:
    def __init__(self, payload, links=None, status=200):
        self._payload = payload
        self.status_code = status
        self.links = links or {}
        self.text = str(payload)

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_resp_raise_for_status():
    Resp({}).raise_for_status()


def test_fetch_contributions(monkeypatch):
    def fake_get(url, headers, timeout):
        data = {
            "items": [
                {
                    "repository": {"full_name": "o/r"},
                    "commit": {"author": {"date": "2024-01-01T00:00:00Z"}},
                    "sha": "a",
                    "html_url": "u",
                }
            ]
        }
        return Resp(data)

    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setattr(gh_graphql.requests, "get", fake_get)
    out = gh_graphql.fetch_contributions("me", "2024-01-01", "2024-12-31")
    assert out[0]["sha"] == "a"


def test_fetch_contributions_errors(monkeypatch):
    def fake_get(url, headers, timeout):
        return Resp({"message": "Bad credentials"}, status=401)

    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setattr(gh_graphql.requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        gh_graphql.fetch_contributions("me", "2024-01-01", "2024-12-31")


def test_generate_heatmap_writes_files(monkeypatch, tmp_path):
    def fake_fetch(login, start, end):
        return [
            {
                "repo": "o/r",
                "occurredAt": "2024-01-01T00:00:00Z",
                "sha": "a",
                "url": "u",
            }
        ]

    def fake_stats(owner, repo, sha):
        return {"additions": 5, "deletions": 5}

    monkeypatch.setattr(generate_heatmap, "fetch_contributions", fake_fetch)
    monkeypatch.setattr(generate_heatmap, "fetch_commit_stats", fake_stats)
    monkeypatch.chdir(tmp_path)
    generate_heatmap.main()
    assert (tmp_path / "assets/heatmap_light.svg").exists()
    assert (tmp_path / "assets/heatmap_dark.svg").exists()


def test_generate_heatmap_skips_without_token(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    generate_heatmap.main()
    captured = capsys.readouterr()
    assert "Skipping heatmap generation" in captured.err
    assert not (tmp_path / "assets/heatmap_light.svg").exists()
    assert not (tmp_path / "assets/heatmap_dark.svg").exists()
