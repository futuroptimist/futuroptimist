from pathlib import Path
import sys
import types

import src.generate_annual_contribs as wrapper


def test_wrapper_main(monkeypatch, tmp_path):
    called = {}

    def fake_fetch_counts():
        called["fetch"] = True
        return {2024: 1}

    def fake_chart(counts, output):
        called["out"] = Path(output)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("svg")

    def fake_csv(counts):
        called["csv"] = True

    monkeypatch.setattr(
        wrapper,
        "base",
        types.SimpleNamespace(
            fetch_counts=fake_fetch_counts,
            generate_chart=fake_chart,
            write_csv=fake_csv,
            SVG_OUTPUT=tmp_path / "default.svg",
        ),
    )
    out = tmp_path / "chart.svg"
    monkeypatch.setattr(sys, "argv", ["x", "--out", str(out)])
    wrapper.main()
    assert out.read_text() == "svg"
    assert called["out"] == out
    assert called["csv"]
