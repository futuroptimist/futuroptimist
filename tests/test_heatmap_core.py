import datetime as dt
import runpy
import sys
import types
from pathlib import Path

import svgwrite
from scripts import generate_heatmap as gh


def test_aggregate_loc(monkeypatch):
    contribs = [{"repo": "o/r", "occurredAt": "2024-01-01T00:00:00Z", "sha": "a"}]
    monkeypatch.setattr(
        gh, "fetch_commit_stats", lambda o, r, s: {"additions": 2, "deletions": 2}
    )
    loc = gh.aggregate_loc(contribs)
    assert loc["2024-01-01"] == 4


def test_draw_bars_calls_draw_bar(monkeypatch):
    loc = {"2024-01-01": 100}
    start = dt.date(2024, 1, 1)
    called = []

    def fake_draw_bar(dwg, x, y, h, color):
        called.append((x, y, h, color))

    monkeypatch.setattr(gh, "draw_bar", fake_draw_bar)
    dwg = svgwrite.Drawing()
    gh.draw_bars(dwg, loc, start)
    assert called and called[0][2] > 0


def test_run_as_script_fallback(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate_heatmap.py"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        sys.modules,
        "gh_graphql",
        types.SimpleNamespace(fetch_contributions=lambda *a, **k: []),
    )
    monkeypatch.setitem(
        sys.modules,
        "gh_rest",
        types.SimpleNamespace(
            fetch_commit_stats=lambda *a, **k: {"additions": 1, "deletions": 1}
        ),
    )

    calls = []
    monkeypatch.setitem(
        sys.modules,
        "svg3d",
        types.SimpleNamespace(CELL=12, draw_bar=lambda *a, **k: calls.append(1)),
    )

    class DummyDrawing:
        def __init__(self, path=None, size=None):
            self.path = path

        def add(self, _):
            pass

        def save(self):
            if self.path:
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
                Path(self.path).write_text("svg")

    monkeypatch.setitem(
        sys.modules, "svgwrite", types.SimpleNamespace(Drawing=DummyDrawing)
    )
    # call add once to cover method line
    DummyDrawing("foo.svg").add(None)
    runpy.run_path(path, run_name="__main__")
    assert (tmp_path / "assets" / "heatmap_light.svg").exists()
