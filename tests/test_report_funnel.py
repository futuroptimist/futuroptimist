from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import report_funnel
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
    assert manifest["selected_assets"] == [
        {
            "path": f"footage/{slug}/converted",
            "kind": "directory_select",
        },
        {"path": f"footage/{slug}/converted/clip.png", "kind": "image"},
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


def test_build_manifest_classifies_unknown_extension_as_other(tmp_path: Path) -> None:
    root = tmp_path / "footage"
    slug = "20280101_future"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    unknown = converted / "notes.txt"
    unknown.write_text("reference")

    selects = tmp_path / "selects.txt"
    selects.write_text("converted/notes.txt")

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_assets"] == [
        {"path": f"footage/{slug}/converted/notes.txt", "kind": "other"}
    ]


def test_build_manifest_canonicalizes_repo_relative_paths(tmp_path: Path) -> None:
    root = tmp_path / "media"
    slug = "20270303_demo"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    asset = converted / "still.png"
    asset.write_text("x", encoding="utf-8")

    selects = tmp_path / "selects.txt"
    selects.write_text(asset.resolve().as_posix())

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_assets"] == [
        {"path": f"footage/{slug}/converted/still.png", "kind": "image"}
    ]


def test_build_manifest_handles_windows_paths(tmp_path: Path) -> None:
    root = tmp_path / "footage"
    slug = "20251001_demo"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    asset = converted / "clip.png"
    asset.write_bytes(b"x")

    selects = tmp_path / "selects.txt"
    selects.write_text(
        "\n".join(
            [
                "converted\\\\clip.png",
                f"C:\\\\repo\\\\footage\\\\{slug}\\\\converted\\\\clip.png",
            ]
        )
    )

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_assets"] == [
        {"path": f"footage/{slug}/converted/clip.png", "kind": "image"}
    ]
    assert manifest["selected_count"] == 1


def test_build_manifest_handles_windows_paths_with_repo_prefix(tmp_path: Path) -> None:
    root = tmp_path / "footage"
    slug = "20251130_repo"
    converted = root / slug / "converted"
    converted.mkdir(parents=True)
    asset = converted / "clip.png"
    asset.write_bytes(b"x")

    selects = tmp_path / "selects.txt"
    selects.write_text(
        "\n".join(
            [
                f"C:\\\\Users\\\\me\\\\project\\\\footage\\\\{slug}\\\\converted\\\\clip.png",
            ]
        )
    )

    manifest = build_manifest(root, slug, selects)
    assert manifest["selected_assets"] == [
        {"path": f"footage/{slug}/converted/clip.png", "kind": "image"}
    ]
    assert manifest["selected_count"] == 1


def test_main_reports_stats(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "footage"
    slug = "20251225_demo"
    originals = root / slug / "originals"
    converted = root / slug / "converted"
    originals.mkdir(parents=True)
    converted.mkdir()

    for name in ["a.heic", "b.mov", "c.jpg"]:
        (originals / name).write_text("x", encoding="utf-8")
    for name in ["a.png", "b.mp4"]:
        (converted / name).write_text("y", encoding="utf-8")

    selects = tmp_path / "selects.txt"
    selects.write_text("converted/a.png\n", encoding="utf-8")
    output = tmp_path / "selections.json"

    exit_code = report_funnel.main(
        [
            "--slug",
            slug,
            "--root",
            str(root),
            "--selects-file",
            str(selects),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Originals: 3" in captured.out
    assert "Converted: 2" in captured.out
    assert "Selected: 1" in captured.out

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["converted_coverage"] == pytest.approx(2 / 3, rel=1e-6)
    assert data["selected_coverage"] == pytest.approx(0.5, rel=1e-6)
