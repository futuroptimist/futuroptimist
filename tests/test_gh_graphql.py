import pytest
import src.gh_graphql as gh


class Resp:
    def __init__(self, payload, links=None):
        self._payload = payload
        self.status_code = 200
        self.links = links or {}
        self.text = str(payload)

    def json(self):
        return self._payload


def test_fetch_contributions_pagination(monkeypatch):
    responses = []

    def fake_get(url, headers, timeout):
        if not responses:
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
            resp = Resp(data, links={"next": {}})
        else:
            data = {
                "items": [
                    {
                        "repository": {"full_name": "o/r2"},
                        "commit": {"author": {"date": "2024-01-02T00:00:00Z"}},
                        "sha": "b",
                        "html_url": "v",
                    }
                ]
            }
            resp = Resp(data)
        responses.append(resp)
        return resp

    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setattr(gh.requests, "get", fake_get)
    out = gh.fetch_contributions("me", "2024-01-01", "2024-12-31")
    assert [c["sha"] for c in out] == ["a", "b"]


def test_fetch_contributions_falls_back_to_github_token(monkeypatch):
    def fake_get(url, headers, timeout):
        assert headers["Authorization"] == "Bearer y"
        return Resp({"items": []})

    monkeypatch.setenv("GITHUB_TOKEN", "y")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(gh.requests, "get", fake_get)
    assert gh.fetch_contributions("me", "2024-01-01", "2024-12-31") == []


def test_fetch_contributions_missing_token(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(EnvironmentError):
        gh.fetch_contributions("me", "2024-01-01", "2024-12-31")
