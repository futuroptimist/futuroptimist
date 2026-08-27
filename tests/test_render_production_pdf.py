from pathlib import Path

import pytest
from pypdf import PdfReader

from src import render_production_pdf as renderer


def add_plan(root: Path, slug: str, names=("plan.md",)) -> Path:
    slug_dir = root / "video_scripts" / slug
    production = slug_dir / "production"
    production.mkdir(parents=True)
    for name in names:
        (production / name).write_text(f"# {name}\n\n- [ ] item\n", encoding="utf-8")
    return slug_dir


def test_discovery_is_deterministic_and_requires_a_direct_markdown(tmp_path):
    root = tmp_path / "video_scripts"
    add_plan(tmp_path, "Zulu")
    add_plan(tmp_path, "alpha")
    empty = root / "empty" / "production"
    empty.mkdir(parents=True)
    (empty / "nested").mkdir()
    (empty / "nested" / "ignored.md").write_text("# no\n")
    assert renderer.discover_eligible(root) == ["alpha", "Zulu"]


def test_latest_uses_valid_date_then_case_insensitive_full_slug_tiebreak(tmp_path):
    scripts = tmp_path / "video_scripts"
    add_plan(tmp_path, "20250101_old")
    add_plan(tmp_path, "20260101_alpha")
    add_plan(tmp_path, "20260101_Zulu")
    add_plan(tmp_path, "20261301_invalid")
    assert renderer.resolve_slug("latest", scripts) == "20260101_Zulu"
    add_plan(tmp_path, "20270101_new")
    assert renderer.resolve_slug("latest", scripts) == "20270101_new"


def test_latest_fails_without_a_dated_eligible_directory(tmp_path):
    scripts = tmp_path / "video_scripts"
    add_plan(tmp_path, "undated")
    with pytest.raises(renderer.ProductionPDFError, match="latest requires"):
        renderer.resolve_slug("latest", scripts)


@pytest.mark.parametrize("selector", ["", "/tmp/x", "../x", "a/b", r"a\b", ".", ".."])
def test_exact_selector_rejects_paths_and_prints_all_eligible(tmp_path, selector):
    scripts = tmp_path / "video_scripts"
    add_plan(tmp_path, "one")
    add_plan(tmp_path, "two")
    with pytest.raises(renderer.ProductionPDFError) as caught:
        renderer.resolve_slug(selector, scripts)
    assert "one" in str(caught.value) and "two" in str(caught.value)


def test_exact_validation_rejects_missing_empty_and_symlink_escape(tmp_path):
    scripts = tmp_path / "video_scripts"
    add_plan(tmp_path, "valid")
    (scripts / "empty" / "production").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "plan.md").write_text("# outside\n")
    (scripts / "escape").mkdir()
    (scripts / "escape" / "production").symlink_to(outside, target_is_directory=True)
    assert renderer.resolve_slug("valid", scripts) == "valid"
    for selector in ("missing", "empty", "escape"):
        with pytest.raises(renderer.ProductionPDFError):
            renderer.resolve_slug(selector, scripts)


def test_footage_links_order_valid_direct_files_then_lexical_remainder(tmp_path):
    scripts = tmp_path / "video_scripts"
    slug_dir = add_plan(tmp_path, "20250101_demo", ("z.md", "A.md", "b.md"))
    slug_dir.joinpath("footage.md").write_text(
        "[B](production/b.md) [again](production/b.md) "
        "[nested](production/nested/x.md) [missing](production/no.md) "
        "[external](https://example.com/production/z.md) "
        "[escape](production/../z.md) [Z](production/z.md)\n",
        encoding="utf-8",
    )
    assert [
        path.name for path in renderer.ordered_sources("20250101_demo", scripts)
    ] == [
        "b.md",
        "z.md",
        "A.md",
    ]


def test_lexical_fallback_without_usable_links(tmp_path):
    scripts = tmp_path / "video_scripts"
    add_plan(tmp_path, "demo", ("z.md", "A.md", "b.md"))
    assert [path.name for path in renderer.ordered_sources("demo", scripts)] == [
        "A.md",
        "b.md",
        "z.md",
    ]


def test_status_markers_only_change_real_list_item_text():
    markdown = """- [ ] empty
- [x] checked
- [-] progress
- [!] blocked
- `[ ] inline`

```text
- [x] fenced
```
"""
    rendered = renderer.markdown_parser().render(markdown)
    for status in ("empty", "checked", "progress", "blocked"):
        assert f"status-{status}" in rendered
    assert "<code>[ ] inline</code>" in rendered
    assert "- [x] fenced" in rendered


def test_html_has_tables_unicode_sections_and_page_boundary(tmp_path):
    slug_dir = add_plan(tmp_path, "demo", ("one.md", "two.md"))
    first = slug_dir / "production" / "one.md"
    first.write_text(
        "# Arrow →\n\n| A | B |\n|---|---|\n| value — ok | **bold** |\n",
        encoding="utf-8",
    )
    sources = renderer.ordered_sources("demo", tmp_path / "video_scripts")
    html = renderer.build_html("demo", sources, tmp_path)
    assert html.count('<section class="production-document"') == 2
    assert "<table>" in html and "Arrow →" in html
    css = renderer.STYLESHEET.read_text(encoding="utf-8")
    assert ".production-document + .production-document { break-before: page; }" in css


def test_default_output_uses_resolved_slug(tmp_path):
    assert renderer.default_output("20250101_demo", tmp_path) == (
        tmp_path / "dist/production-pdfs/20250101_demo-production-checklist.pdf"
    )


def test_atomic_failure_preserves_output_and_sources(tmp_path, monkeypatch):
    slug_dir = add_plan(tmp_path, "20250101_demo")
    source = slug_dir / "production" / "plan.md"
    before = source.read_bytes()
    output = tmp_path / "existing.pdf"
    output.write_bytes(b"old")

    def fail(*args, **kwargs):
        raise RuntimeError("render failed")

    monkeypatch.setattr(renderer.HTML, "write_pdf", fail)
    with pytest.raises(RuntimeError, match="render failed"):
        renderer.render_pdf("20250101_demo", output, repo_root=tmp_path)
    assert output.read_bytes() == b"old"
    assert source.read_bytes() == before


def test_list_cli_reports_eligible_and_latest(capsys):
    assert renderer.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "20260901_sugarkube" in output
    assert "latest -> 20260901_sugarkube" in output


def test_real_sugarkube_pdf_smoke(tmp_path):
    output = tmp_path / "sugarkube.pdf"
    result = renderer.render_pdf("latest", output)
    assert result.resolved_slug == "20260901_sugarkube"
    assert [Path(path).name for path in result.sources] == [
        "broll.md",
        "stock.md",
        "graphics.md",
    ]
    assert output.read_bytes().startswith(b"%PDF-")
    reader = PdfReader(output)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert len(reader.pages) >= 3
    titles = [
        "Sugarkube Original Footage Plan",
        "Sugarkube Third-Party Media Plan",
        "Sugarkube Manual Graphics Plan",
    ]
    positions = [text.index(title) for title in titles]
    assert positions == sorted(positions)
    for expected in ("A04", "C09", "T06", "G19", "Rights ledger"):
        assert expected in text
