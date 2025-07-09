from pathlib import Path
import sys
import types

import src.generate_contrib_heatmap as gh


def test_generate_heatmap_no_dates(monkeypatch, tmp_path):
    saved = {}

    class FakeFig:
        def set_size_inches(self, w, h):
            saved["size"] = (w, h)

        def savefig(self, path, bbox_inches=None, transparent=None):
            Path(path).write_text("svg")
            saved["path"] = Path(path)

    class FakeAx:
        def __init__(self):
            self.figure = FakeFig()

        def get_figure(self):
            return self.figure

    monkeypatch.setattr(
        gh.calplot,
        "yearplot",
        lambda series, year, cmap="Greens", linewidth=0.5: FakeAx(),
    )
    out = tmp_path / "h.svg"
    gh.generate_heatmap([], 2024, out)
    assert out.read_text() == "svg"


def test_main_entrypoint(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GH_TOKEN", "x")
    monkeypatch.setattr(gh, "fetch_pr_dates", lambda y: [])
    monkeypatch.setattr(gh, "OUTPUT_PATH", Path("assets/h.svg"))

    def fake_generate(dates, year, output=gh.OUTPUT_PATH):
        output.parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("x")

    monkeypatch.setattr(gh, "generate_heatmap", fake_generate)
    gh.main()
    assert (tmp_path / "assets/h.svg").exists()


def test_entrypoint_exec(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    path = Path(__file__).resolve().parents[1] / "src" / "generate_contrib_heatmap.py"
    monkeypatch.setenv("GH_TOKEN", "x")
    req = types.SimpleNamespace(
        post=lambda *a, **k: types.SimpleNamespace(
            status_code=200,
            json=lambda: {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "pullRequestContributions": {
                                "edges": [],
                                "pageInfo": {"hasNextPage": False},
                            }
                        }
                    }
                }
            },
            raise_for_status=lambda: None,
        )
    )
    monkeypatch.setitem(sys.modules, "requests", req)
    ns = {
        "__name__": "__main__",
        "__file__": str(path),
        "__package__": None,
        "fetch_pr_dates": lambda y: [],
        "generate_heatmap": lambda d, y, output=Path("assets/pr_heatmap.svg"): Path(
            output
        ).write_text("x"),
        "requests": req,
    }
    code = compile(path.read_text(), str(path), "exec")
    exec(code, ns)
    assert (tmp_path / "assets/pr_heatmap.svg").exists()
