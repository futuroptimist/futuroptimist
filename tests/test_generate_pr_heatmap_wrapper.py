from pathlib import Path
import sys
import types

import src.generate_pr_heatmap as wrapper


def test_wrapper_main(monkeypatch, tmp_path):
    called = {}

    def fake_fetch(year):
        called["year"] = year
        return ["d"]

    def fake_generate(dates, year, output):
        called["dates"] = dates
        called["out"] = Path(output)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("svg")

    monkeypatch.setattr(
        wrapper,
        "base",
        types.SimpleNamespace(
            fetch_pr_dates=fake_fetch,
            generate_heatmap=fake_generate,
            OUTPUT_PATH=tmp_path / "default.svg",
        ),
    )
    out = tmp_path / "o.svg"
    monkeypatch.setattr(sys, "argv", ["x", "--out", str(out)])
    wrapper.main()
    assert out.read_text() == "svg"
    assert called["out"] == out
