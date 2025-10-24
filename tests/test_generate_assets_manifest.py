from __future__ import annotations

import json
import pathlib
import warnings

import pytest

import src.generate_assets_manifest as gam


def _read_manifest(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_generate_manifest_writes_assets_json(tmp_path: pathlib.Path) -> None:
    repo = tmp_path
    video_root = repo / "video_scripts"
    footage_root = repo / "footage"
    slug = "20251224_solstice-special"

    (video_root / slug).mkdir(parents=True)
    (video_root / slug / "notes.md").write_text("shoot notes", encoding="utf-8")

    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)
    (converted / "a.mp4").write_bytes(b"video")
    (converted / "stills" / "frame.jpg").parent.mkdir(parents=True)
    (converted / "stills" / "frame.jpg").write_bytes(b"img")

    audio = footage_root / slug / "audio"
    audio.mkdir(parents=True)
    (audio / "voice.wav").write_bytes(b"audio")

    (footage_root / slug / "labels.json").write_text("[]", encoding="utf-8")

    results = gam.generate_manifests(
        video_root=video_root,
        footage_root=footage_root,
        slugs=[slug],
        overwrite=True,
    )

    manifest_path = video_root / slug / "assets.json"
    assert manifest_path.exists(), "Expected assets.json to be created"

    manifest = _read_manifest(manifest_path)
    expected_dirs = {
        f"footage/{slug}",
        f"footage/{slug}/converted",
        f"footage/{slug}/converted/stills",
        f"footage/{slug}/audio",
    }
    assert set(manifest["footage_dirs"]) == expected_dirs
    assert manifest["labels_files"] == [f"footage/{slug}/labels.json"]
    assert manifest["notes_file"] == f"video_scripts/{slug}/notes.md"

    assert results == [
        {
            "slug": slug,
            "written": True,
            "path": manifest_path,
            "footage_dirs": sorted(expected_dirs),
        }
    ]


def test_generate_manifest_detects_notes_txt_in_footage(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path
    video_root = repo / "video_scripts"
    footage_root = repo / "footage"
    slug = "20260101_future-build"

    (video_root / slug).mkdir(parents=True)

    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)
    (converted / "clip.mp4").write_bytes(b"video")

    notes_txt = footage_root / slug / "notes.txt"
    notes_txt.write_text("shot notes", encoding="utf-8")

    gam.generate_manifests(
        video_root=video_root,
        footage_root=footage_root,
        slugs=[slug],
        overwrite=True,
    )

    manifest = _read_manifest(video_root / slug / "assets.json")
    assert manifest["notes_file"] == f"footage/{slug}/notes.txt"


def test_generate_manifest_skips_existing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path
    video_root = repo / "video_scripts"
    footage_root = repo / "footage"
    slug = "20240101_new-year"

    (video_root / slug).mkdir(parents=True)
    existing = {"footage_dirs": [f"footage/{slug}"]}
    (video_root / slug / "assets.json").write_text(
        json.dumps(existing), encoding="utf-8"
    )

    (footage_root / slug).mkdir(parents=True)
    (footage_root / slug / "clip.mp4").write_bytes(b"video")

    results = gam.generate_manifests(
        video_root=video_root,
        footage_root=footage_root,
        slugs=[slug],
        overwrite=False,
    )

    captured = capsys.readouterr()
    assert "Skipping" in captured.out

    manifest_path = video_root / slug / "assets.json"
    assert _read_manifest(manifest_path) == existing
    assert results == [
        {
            "slug": slug,
            "written": False,
            "path": manifest_path,
            "footage_dirs": [f"footage/{slug}"],
        }
    ]


def test_cli_respects_dry_run(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path
    slug = "20240214_valentines"
    (repo / "video_scripts" / slug).mkdir(parents=True)
    converted = repo / "footage" / slug / "converted"
    converted.mkdir(parents=True)
    (converted / "shot.mov").write_bytes(b"v")

    monkeypatch.chdir(repo)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exit_code = gam.main(["--slug", slug, "--dry-run"])

    assert exit_code == 0
    assert not (repo / "video_scripts" / slug / "assets.json").exists()
