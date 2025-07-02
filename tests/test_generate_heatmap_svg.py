import pytest
from scripts import gh_graphql, generate_heatmap


class Resp:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_contributions(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append(json["variables"]["cursor"])
        if json["variables"]["cursor"] is None:
            data = {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "commitContributionsByRepository": {
                                "pageInfo": {"hasNextPage": True, "endCursor": "C1"},
                                "nodes": [
                                    {
                                        "repository": {"nameWithOwner": "o/r"},
                                        "contributions": {
                                            "nodes": [
                                                {
                                                    "occurredAt": "2024-01-01T00:00:00Z",
                                                    "commit": {"oid": "a", "url": "u"},
                                                }
                                            ]
                                        },
                                    }
                                ],
                            }
                        }
                    }
                }
            }
        else:
            data = {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "commitContributionsByRepository": {
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                                "nodes": [],
                            }
                        }
                    }
                }
            }
        return Resp(data)

    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setattr(gh_graphql.requests, "post", fake_post)
    out = gh_graphql.fetch_contributions("me", "2024-01-01", "2024-12-31")
    assert out[0]["sha"] == "a"
    assert calls == [None, "C1"]


def test_fetch_contributions_errors(monkeypatch):
    def fake_post(url, json, headers, timeout):
        return Resp({"message": "Bad credentials"})

    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setattr(gh_graphql.requests, "post", fake_post)
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
