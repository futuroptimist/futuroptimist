from pathlib import Path

import pytest
from pypdf import PdfReader

from src import render_production_pdf as pdf


def episode(root: Path, slug: str, files=("z.md",)) -> Path:
    production = root / slug / "production"
    production.mkdir(parents=True)
    for name in files:
        (production / name).write_text(
            f"# {name}\n\n- [ ] item → `[-]`\n", encoding="utf-8"
        )
    return root / slug


def test_discovery_sorting_and_latest_are_dynamic(tmp_path):
    episode(tmp_path, "20250101_z")
    episode(tmp_path, "20250101_A")
    episode(tmp_path, "notes")
    assert pdf.discover_eligible(tmp_path) == ["20250101_A", "20250101_z", "notes"]
    assert pdf.resolve_slug("latest", tmp_path) == "20250101_z"
    episode(tmp_path, "20260101_new")
    assert pdf.resolve_slug("latest", tmp_path) == "20260101_new"


@pytest.mark.parametrize("selector", ["../bad", "a/b", "a\\b", "/tmp/bad", "missing"])
def test_invalid_exact_selector_lists_eligible(tmp_path, selector):
    episode(tmp_path, "20250101_good")
    with pytest.raises(pdf.ProductionPDFError, match="20250101_good"):
        pdf.resolve_slug(selector, tmp_path)


def test_latest_requires_valid_date(tmp_path):
    episode(tmp_path, "undated")
    episode(tmp_path, "20250230_bad-date")
    with pytest.raises(pdf.ProductionPDFError, match="no dated eligible"):
        pdf.resolve_slug("latest", tmp_path)


def test_symlinks_and_empty_directories_are_ineligible(tmp_path):
    (tmp_path / "empty" / "production").mkdir(parents=True)
    outside = episode(tmp_path.parent / "outside", "20250101_escape")
    (tmp_path / "20250101_link").symlink_to(outside, target_is_directory=True)
    assert pdf.discover_eligible(tmp_path) == []


def test_footage_links_order_valid_direct_unique_files(tmp_path):
    item = episode(tmp_path, "20250101_plan", ("b.md", "A.md", "c.md"))
    (item / "footage.md").write_text(
        "[b](production/b.md) [dup](production/b.md) [nested](production/x/c.md) "
        "[missing](production/no.md) [escape](../production/A.md) "
        "[external](https://example.com/production/A.md)\n",
        encoding="utf-8",
    )
    assert [path.name for path in pdf.ordered_sources("20250101_plan", tmp_path)] == [
        "b.md",
        "A.md",
        "c.md",
    ]


def test_task_markers_only_change_list_item_text():
    source = "\n".join(
        [
            "- [ ] open",
            "- [x] done",
            "- [-] doing",
            "- [!] blocked",
            "- `[ ]` code",
            "",
            "```",
            "- [x] fenced",
            "```",
        ]
    )
    rendered = pdf.markdown_renderer().render(source)
    assert all(
        f"status-{state}" in rendered
        for state in ("empty", "checked", "progress", "blocked")
    )
    assert "<code>[ ]</code>" in rendered
    assert "- [x] fenced" in rendered


def test_html_has_sections_page_boundaries_tables_and_unicode(tmp_path):
    item = episode(tmp_path, "20250101_plan", ("a.md", "b.md"))
    (item / "production" / "a.md").write_text(
        "# Arrow →\n\n| A | B |\n|---|---|\n| ✓ | — |\n", encoding="utf-8"
    )
    html = pdf.build_html(
        "20250101_plan", pdf.ordered_sources("20250101_plan", tmp_path)
    )
    assert html.count('class="production-document"') == 2
    assert "<table>" in html and "Arrow →" in html


def test_real_sugarkube_pdf_smoke_and_default_name(tmp_path):
    result = pdf.render("20260901_sugarkube", tmp_path / "plan.pdf")
    assert result.sources[-1].endswith("graphics.md")
    reader = PdfReader(result.output)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    headings = [
        "Sugarkube Original Footage Plan",
        "Sugarkube Third-Party Media Plan",
        "Sugarkube Manual Graphics Plan",
    ]
    assert all(heading in text for heading in headings)
    assert [text.index(heading) for heading in headings] == sorted(
        text.index(heading) for heading in headings
    )
    assert all(asset in text for asset in ("A04", "C09", "T06", "G19", "Rights ledger"))
    assert len(reader.pages) >= 3


def test_atomic_failure_preserves_output_and_source(tmp_path, monkeypatch):
    root = tmp_path / "video_scripts"
    item = episode(root, "20250101_plan")
    source = item / "production" / "z.md"
    before = source.read_bytes()
    output = tmp_path / "existing.pdf"
    output.write_bytes(b"old")
    monkeypatch.setattr(
        pdf.HTML,
        "write_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(RuntimeError, match="boom"):
        pdf.render("20250101_plan", output, video_scripts=root)
    assert output.read_bytes() == b"old"
    assert source.read_bytes() == before


def test_list_cli(capsys):
    assert pdf.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "20260901_sugarkube" in output
    assert "latest -> 20260901_sugarkube" in output
