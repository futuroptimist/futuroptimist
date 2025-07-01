import pathlib
from scripts import generate_contrib_heatmap as gh


class Resp:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_pr_dates_handles_pagination(monkeypatch):
    def fake_post(url, json, headers, timeout):
        after = json["variables"]["after"]
        if after is None:
            data = {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "pullRequestContributions": {
                                "edges": [
                                    {
                                        "node": {
                                            "occurredAt": "2024-01-01T00:00:00Z",
                                            "pullRequest": {
                                                "repository": {
                                                    "owner": {"login": "futuroptimist"}
                                                }
                                            },
                                        }
                                    }
                                ],
                                "pageInfo": {"hasNextPage": True, "endCursor": "C1"},
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
                            "pullRequestContributions": {
                                "edges": [
                                    {
                                        "node": {
                                            "occurredAt": "2024-01-02T00:00:00Z",
                                            "pullRequest": {
                                                "repository": {
                                                    "owner": {
                                                        "login": "democratizedspace"
                                                    }
                                                }
                                            },
                                        }
                                    }
                                ],
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                            }
                        }
                    }
                }
            }
        return Resp(data)

    monkeypatch.setattr(gh.requests, "post", fake_post)
    monkeypatch.setenv("GH_TOKEN", "x")
    dates = gh.fetch_pr_dates(2024)
    assert dates == ["2024-01-01", "2024-01-02"]


def test_generate_heatmap_writes_file(monkeypatch, tmp_path):
    saved = {}

    class FakeFig:
        def set_size_inches(self, w, h):
            saved["size"] = (w, h)

        def savefig(self, path, bbox_inches=None, transparent=None):
            saved["path"] = pathlib.Path(path)
            saved["path"].write_text("svg")

    class FakeAx:
        def __init__(self):
            self.figure = FakeFig()

        def get_figure(self):
            return self.figure

    def fake_yearplot(series, year, cmap="Greens", linewidth=0.5):
        saved["year"] = year
        return FakeAx()

    monkeypatch.setattr(gh.calplot, "yearplot", fake_yearplot)
    out = tmp_path / "h.svg"
    gh.generate_heatmap(["2024-01-01"], 2024, out)
    assert out.read_text() == "svg"
    assert saved["year"] == 2024
    assert saved["path"] == out
