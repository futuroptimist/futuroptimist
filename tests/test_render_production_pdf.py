from pathlib import Path

import pytest
from pypdf import PdfReader

from src import render_production_pdf as pdf


def plan(root: Path, slug: str, files=("z.md",)) -> Path:
    directory = root / slug / "production"
    directory.mkdir(parents=True)
    for name in files:
        (directory / name).write_text(
            f"# {name}\n\n- [ ] item → `[-]`\n", encoding="utf-8"
        )
    return root / slug


def test_discovery_sorting_resolution_and_dynamic_latest(tmp_path):
    plan(tmp_path, "undated")
    plan(tmp_path, "20250101_Zed")
    plan(tmp_path, "20250101_alpha")
    assert pdf.discover_eligible(tmp_path) == [
        "20250101_alpha",
        "20250101_Zed",
        "undated",
    ]
    assert pdf.resolve_slug("latest", tmp_path) == "20250101_Zed"
    plan(tmp_path, "20270101_new")
    assert pdf.resolve_slug("latest", tmp_path) == "20270101_new"


def test_latest_requires_valid_date(tmp_path):
    plan(tmp_path, "20250230_bad")
    with pytest.raises(pdf.ProductionPDFError, match="no dated"):
        pdf.resolve_slug("latest", tmp_path)


@pytest.mark.parametrize("selector", ["/tmp/x", "../x", "a/b", r"a\\b", ".", "missing"])
def test_rejects_unsafe_or_ineligible_exact_slug(tmp_path, selector):
    plan(tmp_path, "20250101_ok")
    with pytest.raises(pdf.ProductionPDFError):
        pdf.resolve_slug(selector, tmp_path)


def test_empty_and_symlink_directories_are_not_eligible(tmp_path):
    (tmp_path / "20250101_empty" / "production").mkdir(parents=True)
    outside = tmp_path / "outside"
    plan(outside, "target")
    (tmp_path / "20250102_link").symlink_to(
        outside / "target", target_is_directory=True
    )
    assert pdf.discover_eligible(tmp_path) == []


def test_footage_order_ignores_duplicate_and_unsafe_links(tmp_path):
    slug = plan(tmp_path, "20250101_demo", ("B.md", "a.md", "extra.md"))
    (slug / "production" / "nested").mkdir()
    (slug / "production" / "nested" / "bad.md").write_text("bad")
    (slug / "footage.md").write_text(
        "[B](production/B.md) [again](production/B.md) [missing](production/no.md) "
        "[nested](production/nested/bad.md) [escape](../x.md) [web](https://example.com/a.md) "
        "[A](production/a.md)\n",
        encoding="utf-8",
    )
    assert [p.name for p in pdf.ordered_sources(slug.name, tmp_path)] == [
        "B.md",
        "a.md",
        "extra.md",
    ]


def test_lexical_fallback_is_case_insensitive(tmp_path):
    slug = plan(tmp_path, "20250101_demo", ("z.md", "A.md", "b.md"))
    assert [p.name for p in pdf.ordered_sources(slug.name, tmp_path)] == [
        "A.md",
        "b.md",
        "z.md",
    ]


def test_markers_only_change_list_item_prefixes_and_support_markdown():
    source = """# Unicode →

- [ ] empty
- [x] done
- [-] progress
- [!] blocked

`[-] inline`

```text
- [x] fenced
```

| A | B |
|---|---|
| **bold** | *italic* |
"""
    html = pdf.build_html("slug", [FakeSource(source)])
    for status in ("empty", "checked", "progress", "blocked"):
        assert f"status-{status}" in html
    assert "[-] inline" in html
    assert "[x] fenced" in html
    assert "<table>" in html and "Unicode →" in html


class FakeSource:
    name = "fake.md"

    def __init__(self, value):
        self.value = value

    def read_text(self, **_kwargs):
        return self.value


def test_sections_have_page_break_hook():
    html = pdf.build_html("slug", [FakeSource("# One"), FakeSource("# Two")])
    assert html.count('class="production-document"') == 2
    assert ".production-document + .production-document" in pdf.CSS_PATH.read_text()


def test_real_sugarkube_pdf_smoke_and_sources_unchanged(tmp_path):
    sources = pdf.ordered_sources("20260901_sugarkube")
    before = {path: path.read_bytes() for path in sources}
    result = pdf.render("latest", tmp_path / "result.pdf")
    assert result.resolved_slug == "20260901_sugarkube"
    assert [Path(path).name for path in result.source_paths] == [
        "broll.md",
        "stock.md",
        "graphics.md",
    ]
    assert Path(result.output_path).read_bytes().startswith(b"%PDF-")
    reader = PdfReader(result.output_path)
    text = "\n".join(page.extract_text() for page in reader.pages)
    phrases = ["Original Footage", "Third-Party Media", "Manual Graphics"]
    assert [text.index(phrase) for phrase in phrases] == sorted(
        text.index(phrase) for phrase in phrases
    )
    assert all(value in text for value in ("A04", "C09", "T06", "G19", "Rights ledger"))
    assert len(reader.pages) >= 3
    assert before == {path: path.read_bytes() for path in sources}


def test_atomic_failure_preserves_output(tmp_path, monkeypatch):
    plan(tmp_path, "20250101_demo")
    output = tmp_path / "existing.pdf"
    output.write_bytes(b"old")
    monkeypatch.setattr(pdf, "CSS_PATH", tmp_path / "missing.css")
    with pytest.raises(OSError):
        pdf.render("20250101_demo", output, video_scripts=tmp_path)
    assert output.read_bytes() == b"old"


def test_list_cli(capsys):
    assert pdf.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "20260901_sugarkube" in output
    assert "latest -> 20260901_sugarkube" in output
