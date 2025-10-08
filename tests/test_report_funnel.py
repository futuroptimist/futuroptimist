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
    (root / slug / "converted" / "c.wav").write_bytes(b"x")
    selects = tmp_path / "selects.txt"
    selects.write_text(
        "\n".join(["converted/a.png", "converted/b.mp4", "converted/c.wav"])
    )

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_count"] == 3
    kinds = {a["kind"] for a in manifest["selected_assets"]}
    assert kinds == {"image", "video", "audio"}


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


def test_build_manifest_normalizes_slug_prefixed_paths(tmp_path: Path) -> None:
    root = tmp_path / "footage"
    slug = "20260101_future"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    (converted / "clip.png").write_bytes(b"x")
    selects = tmp_path / "selects.txt"
    selects.write_text("\n".join([slug, f"{slug}/clip.png"]))

    manifest = build_manifest(root, slug, selects)
    paths = [entry["path"] for entry in manifest["selected_assets"]]
    assert paths == [
        f"footage/{slug}/converted",
        f"footage/{slug}/converted/clip.png",
    ]


def test_build_manifest_skips_outside_converted_entries(tmp_path: Path) -> None:
    root = tmp_path / "footage"
    slug = "20270202_demo"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    valid = converted / "keep.png"
    valid.write_bytes(b"x")

    outside = tmp_path / "elsewhere" / "clip.png"
    outside.parent.mkdir()
    outside.write_bytes(b"y")

    selects = tmp_path / "selects.txt"
    selects.write_text(
        "\n".join(
            [
                "../sneaky.png",
                outside.as_posix(),
                f"{slug}/../escape.png",
                "converted/../also_bad.mov",
                "converted/keep.png",
            ]
        )
    )

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_count"] == 1
    assert manifest["selected_assets"] == [
        {"path": f"footage/{slug}/converted/keep.png", "kind": "image"}
    ]
