from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.rename_video_slug as rvs


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_rename_video_slug_updates_metadata_and_assets(tmp_path: Path) -> None:
    repo = tmp_path
    video_dir = repo / "video_scripts" / "20240101_old-slug"
    video_dir.mkdir(parents=True)
    (video_dir / "metadata.json").write_text(
        json.dumps(
            {
                "youtube_id": "abc123",
                "title": "Demo",
                "slug": "old-slug",
                "thumbnail": "thumbnails/20240101_old-slug.png",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (video_dir / "assets.json").write_text(
        json.dumps(
            {
                "footage_dirs": [
                    "footage/20240101_old-slug/originals",
                    "footage/20240101_old-slug/converted",
                ],
                "labels_files": [
                    "footage/20240101_old-slug/labels.json",
                ],
                "notes_file": "footage/20240101_old-slug/notes.md",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    footage_dir = repo / "footage" / "20240101_old-slug"
    (footage_dir / "converted").mkdir(parents=True)
    (footage_dir / "labels.json").write_text(
        json.dumps(
            {
                "footage/20240101_old-slug/converted/clip.mp4": {
                    "path": "20240101_old-slug/converted/clip.mp4",
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (footage_dir / "selections.json").write_text(
        json.dumps(
            {
                "slug": "20240101_old-slug",
                "selected_assets": [
                    {
                        "path": "footage/20240101_old-slug/converted/clip.mp4",
                        "kind": "video",
                    }
                ],
                "selected_count": 1,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    dest = rvs.rename_slug("20240101_old-slug", "fresh-slug", repo_root=repo)

    assert dest == repo / "video_scripts" / "20240101_fresh-slug"
    assert not (repo / "video_scripts" / "20240101_old-slug").exists()
    metadata = _read(dest / "metadata.json")
    assert metadata["slug"] == "fresh-slug"
    assert metadata["thumbnail"].endswith("20240101_fresh-slug.png")

    assets = _read(dest / "assets.json")
    assert assets["footage_dirs"] == [
        "footage/20240101_fresh-slug/originals",
        "footage/20240101_fresh-slug/converted",
    ]
    assert assets["notes_file"] == "footage/20240101_fresh-slug/notes.md"

    new_footage = repo / "footage" / "20240101_fresh-slug"
    assert new_footage.exists()
    selections = _read(new_footage / "selections.json")
    assert selections["slug"] == "20240101_fresh-slug"
    assert selections["selected_assets"][0]["path"].startswith(
        "footage/20240101_fresh-slug"
    )
    labels = _read(new_footage / "labels.json")
    assert "20240101_fresh-slug" in next(iter(labels.keys()))


def test_rename_video_slug_dry_run_leaves_structure(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "video_scripts" / "20230101_old").mkdir(parents=True)

    dest = rvs.rename_slug(
        "20230101_old",
        "new-slug",
        repo_root=repo,
        dry_run=True,
    )

    assert dest == repo / "video_scripts" / "20230101_new-slug"
    assert (repo / "video_scripts" / "20230101_old").exists()


def test_rename_video_slug_validates_slug(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "video_scripts" / "20230505_old").mkdir(parents=True)

    with pytest.raises(ValueError):
        rvs.rename_slug("20230505_old", "Bad Slug", repo_root=repo)
