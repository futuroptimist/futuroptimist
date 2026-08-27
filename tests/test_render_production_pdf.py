from pathlib import Path

import pytest
from pypdf import PdfReader

from src import render_production_pdf as pdf


def add_plan(root: Path, slug: str, names=("z.md",)) -> Path:
    folder = root / slug
    production = folder / "production"
    production.mkdir(parents=True)
    for name in names:
        (production / name).write_text(f"# {name}\n\n- [ ] item → `{name}`\n")
    return folder


def test_discovery_sorting_and_latest(tmp_path):
    add_plan(tmp_path, "20260101_Zed")
    add_plan(tmp_path, "20260101_alpha")
    add_plan(tmp_path, "undated")
    assert pdf.discover_eligible(tmp_path) == [
        "20260101_alpha",
        "20260101_Zed",
        "undated",
    ]
    assert pdf.resolve_slug("latest", tmp_path) == "20260101_Zed"
    add_plan(tmp_path, "20270101_new")
    assert pdf.resolve_slug("latest", tmp_path) == "20270101_new"


def test_invalid_exact_and_no_dated_slug(tmp_path):
    add_plan(tmp_path, "undated")
    for selector in ("missing", "../undated", "a/b", "a\\b", str(tmp_path.resolve())):
        with pytest.raises(pdf.ProductionPdfError, match="Eligible slugs"):
            pdf.resolve_slug(selector, tmp_path)
    with pytest.raises(pdf.ProductionPdfError, match="no dated eligible"):
        pdf.resolve_slug("latest", tmp_path)


def test_symlinks_empty_and_nested_files_are_ineligible(tmp_path):
    (tmp_path / "empty" / "production").mkdir(parents=True)
    nested = tmp_path / "nested" / "production" / "child"
    nested.mkdir(parents=True)
    (nested / "only.md").write_text("# nested")
    target = add_plan(tmp_path, "target")
    (tmp_path / "escape").symlink_to(target, target_is_directory=True)
    assert pdf.discover_eligible(tmp_path) == ["target"]


def test_footage_order_ignores_bad_and_duplicate_links(tmp_path):
    folder = add_plan(tmp_path, "20260101_plan", ("alpha.md", "beta.md", "gamma.md"))
    (folder / "footage.md").write_text(
        "[B](production/beta.md) [dup](production/beta.md)\n"
        "[nested](production/sub/alpha.md) [escape](../alpha.md)\n"
        "[external](https://example.com/x.md) [missing](production/no.md)\n"
    )
    assert [path.name for path in pdf.ordered_sources(folder.name, tmp_path)] == [
        "beta.md",
        "alpha.md",
        "gamma.md",
    ]


def test_markers_only_change_list_items_not_code():
    rendered = pdf.markdown_renderer().render(
        "- [ ] empty\n- [x] done\n- [-] doing\n- [!] blocked\n\n"
        "`[x] inline`\n\n```\n- [ ] fenced\n```\n"
    )
    for status in ("empty", "checked", "progress", "blocked"):
        assert f"status-{status}" in rendered
    assert "[x] inline" in rendered
    assert "- [ ] fenced" in rendered


def test_real_sugarkube_pdf_smoke(tmp_path):
    output = tmp_path / "plan.pdf"
    result = pdf.render("latest", output)
    assert result.resolved_slug == "20260901_sugarkube"
    assert [Path(item).name for item in result.included_sources] == [
        "broll.md",
        "stock.md",
        "graphics.md",
    ]
    reader = PdfReader(output)
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) >= 3
    titles = [
        "Sugarkube Original Footage Plan",
        "Sugarkube Third-Party Media Plan",
        "Sugarkube Manual Graphics Plan",
    ]
    assert [text.index(title) for title in titles] == sorted(
        text.index(title) for title in titles
    )
    for phrase in ("A04", "C09", "T06", "G19", "Rights ledger"):
        assert phrase in text


def test_atomic_failure_preserves_output_and_sources(tmp_path, monkeypatch):
    root = tmp_path / "videos"
    folder = add_plan(root, "20260101_plan")
    before = (folder / "production" / "z.md").read_bytes()
    output = tmp_path / "existing.pdf"
    output.write_bytes(b"old")
    monkeypatch.setattr(pdf, "STYLESHEET", tmp_path / "missing.css")
    with pytest.raises(OSError):
        pdf.render("20260101_plan", output, video_scripts=root)
    assert output.read_bytes() == b"old"
    assert (folder / "production" / "z.md").read_bytes() == before


def test_list_cli(capsys):
    assert pdf.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "20260901_sugarkube" in output
    assert "latest -> 20260901_sugarkube" in output
