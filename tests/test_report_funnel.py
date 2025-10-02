from __future__ import annotations

from pathlib import Path

from src.report_funnel import build_manifest


def test_build_manifest_counts(tmp_path: Path):
    root = tmp_path / "footage"
    slug = "20251001_demo"
    (root / slug / "originals").mkdir(parents=True)
    (root / slug / "converted").mkdir(parents=True)
    # originals
    for name in ["a.heic", "b.mov", "c.mp4"]:
        (root / slug / "originals" / name).write_bytes(b"x")
    # converted
    for name in ["a.png", "b.mp4"]:
        (root / slug / "converted" / name).write_bytes(b"x")

    manifest = build_manifest(root, slug, selects_file=None)
    assert manifest["originals_total"] == 3
    assert manifest["converted_total"] == 2
    assert manifest["selected_count"] == 0


def test_build_manifest_with_selects(tmp_path: Path):
    root = tmp_path / "footage"
    slug = "20251001_demo"
    (root / slug / "converted").mkdir(parents=True)
    (root / slug / "converted" / "a.png").write_bytes(b"x")
    (root / slug / "converted" / "b.mp4").write_bytes(b"x")
    selects = tmp_path / "selects.txt"
    selects.write_text("\n".join(["converted/a.png", "converted/b.mp4"]))

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_count"] == 2
    kinds = {a["kind"] for a in manifest["selected_assets"]}
    assert kinds == {"image", "video"}


def test_build_manifest_normalizes_select_paths(tmp_path: Path) -> None:
    root = tmp_path / "footage"
    slug = "20251212_demo"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    (converted / "a.png").write_bytes(b"x")
    (converted / "b.mp4").write_bytes(b"x")
    selects = tmp_path / "selects.txt"
    selects.write_text(
        "\n".join(
            [
                "converted/a.png",
                f"footage/{slug}/converted/b.mp4",
            ]
        )
    )

    manifest = build_manifest(root, slug, selects)
    paths = [entry["path"] for entry in manifest["selected_assets"]]
    assert paths == [
        f"footage/{slug}/converted/a.png",
        f"footage/{slug}/converted/b.mp4",
    ]
