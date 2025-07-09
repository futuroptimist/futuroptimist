from pathlib import Path
import scripts.generate_annual_contributions as mod


def test_fetch_counts(monkeypatch):
    called = []

    def fake_fetch(year):
        called.append(year)
        return ["d"] * year

    monkeypatch.setattr(mod, "fetch_pr_dates", fake_fetch)
    out = mod.fetch_counts(2021, 2023)
    assert out == {2021: 2021, 2022: 2022, 2023: 2023}
    assert called == [2021, 2022, 2023]


def test_generate_chart(tmp_path, monkeypatch):
    recorded = {}

    class FakePlt:
        def figure(self, figsize=None):
            recorded["figsize"] = figsize
            return None

        def bar(self, years, values, color=None):
            recorded["years"] = list(years)
            recorded["values"] = list(values)

        def xticks(self, years):
            recorded["xticks"] = list(years)

        def ylabel(self, label):
            recorded["ylabel"] = label

        def tight_layout(self):
            recorded["tight"] = True

        def savefig(self, path, transparent=None):
            Path(path).write_text("svg")
            recorded["saved"] = Path(path)

    monkeypatch.setattr(mod, "plt", FakePlt())
    out = tmp_path / "c.svg"
    mod.generate_chart({2024: 2}, out)
    assert out.read_text() == "svg"
    assert recorded["years"] == [2024]
    assert recorded["values"] == [2]
    assert recorded["saved"] == out


def test_main(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "fetch_counts", lambda: {2024: 1})

    def fake_generate(counts, output=mod.SVG_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("svg")

    def fake_csv(counts, output=mod.CSV_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("csv")

    monkeypatch.setattr(mod, "generate_chart", fake_generate)
    monkeypatch.setattr(mod, "write_csv", fake_csv)
    mod.main()
    assert (tmp_path / mod.SVG_OUTPUT).exists()
    assert (tmp_path / mod.CSV_OUTPUT).exists()
