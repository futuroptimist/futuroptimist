from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.prepare_youtube_upload as uploader


def _write_metadata(tmp_path: Path, slug: str, metadata: dict) -> Path:
    slug_dir = tmp_path / "video_scripts" / slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    meta_path = slug_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return meta_path


def _ensure_thumbnail(tmp_path: Path, relative_path: str) -> Path:
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"thumbnail")
    return path


def test_build_upload_package_collects_metadata_and_thumbnail(tmp_path: Path) -> None:
    slug = "20250101_test-video"
    thumbnail_rel = "thumbnails/test-video.jpg"
    metadata = {
        "title": "Test Video",
        "description": "Demo description",
        "keywords": ["alpha", "beta"],
        "status": "draft",
        "thumbnail": thumbnail_rel,
    }
    meta_path = _write_metadata(tmp_path, slug, metadata)
    thumb_path = _ensure_thumbnail(tmp_path, thumbnail_rel)

    package = uploader.build_upload_package(slug, repo_root=tmp_path)

    assert package["slug"] == slug
    assert package["metadata_path"] == str(meta_path.resolve())
    assert package["snippet"]["title"] == metadata["title"]
    assert package["snippet"]["description"] == metadata["description"]
    assert package["snippet"]["tags"] == metadata["keywords"]
    assert package["status"]["privacyStatus"] == "private"
    assert package["thumbnail_path"] == str(thumb_path.resolve())
    assert "thumbnail_url" not in package


def test_build_upload_package_accepts_keyword_string(tmp_path: Path) -> None:
    slug = "20250102_second-video"
    thumbnail_rel = "thumbnails/second-video.jpg"
    metadata = {
        "title": "Second Video",
        "description": "Another demo",
        "keywords": "one, two, three",
        "status": "live",
        "thumbnail": thumbnail_rel,
    }
    _write_metadata(tmp_path, slug, metadata)
    _ensure_thumbnail(tmp_path, thumbnail_rel)

    package = uploader.build_upload_package(slug, repo_root=tmp_path)

    assert package["snippet"]["tags"] == ["one", "two", "three"]
    assert package["status"]["privacyStatus"] == "public"


def test_build_upload_package_requires_thumbnail(tmp_path: Path) -> None:
    slug = "20250103_missing-thumb"
    metadata = {
        "title": "Missing Thumb",
        "description": "Thumbnail should be present",
        "keywords": [],
        "status": "draft",
        "thumbnail": "thumbnails/missing.jpg",
    }
    _write_metadata(tmp_path, slug, metadata)

    with pytest.raises(FileNotFoundError):
        uploader.build_upload_package(slug, repo_root=tmp_path)


def test_build_upload_package_respects_privacy_override(tmp_path: Path) -> None:
    slug = "20250104_override"
    thumbnail_rel = "thumbnails/override.jpg"
    metadata = {
        "title": "Override",
        "description": "Override privacy",
        "keywords": [],
        "status": "draft",
        "thumbnail": thumbnail_rel,
    }
    _write_metadata(tmp_path, slug, metadata)
    _ensure_thumbnail(tmp_path, thumbnail_rel)

    package = uploader.build_upload_package(
        slug, repo_root=tmp_path, privacy_override="unlisted"
    )

    assert package["status"]["privacyStatus"] == "unlisted"


def test_build_upload_package_only_schedules_private_videos(tmp_path: Path) -> None:
    slug = "20250106_schedule"
    metadata = {
        "title": "Schedule",
        "description": "Scheduling rules",
        "keywords": [],
        "status": "scheduled",
        "thumbnail": "thumbnails/schedule.jpg",
        "publish_date": "2025-05-01T10:00:00Z",
    }
    _write_metadata(tmp_path, slug, metadata)
    _ensure_thumbnail(tmp_path, "thumbnails/schedule.jpg")

    package = uploader.build_upload_package(slug, repo_root=tmp_path)

    assert package["status"]["privacyStatus"] == "private"
    assert package["status"]["publishAt"] == metadata["publish_date"]

    overridden = uploader.build_upload_package(
        slug, repo_root=tmp_path, privacy_override="unlisted"
    )

    assert overridden["status"]["privacyStatus"] == "unlisted"
    assert "publishAt" not in overridden["status"]


def test_main_writes_output(tmp_path: Path) -> None:
    slug = "20250105_cli"
    thumbnail_rel = "thumbnails/cli.jpg"
    metadata = {
        "title": "CLI",
        "description": "CLI output",
        "keywords": ["cli"],
        "status": "draft",
        "thumbnail": thumbnail_rel,
    }
    _write_metadata(tmp_path, slug, metadata)
    _ensure_thumbnail(tmp_path, thumbnail_rel)

    output_path = tmp_path / "upload.json"

    exit_code = uploader.main(
        [
            "--slug",
            slug,
            "--repo-root",
            str(tmp_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["slug"] == slug
    assert data["thumbnail_path"].endswith("cli.jpg")
    assert data["snippet"]["title"] == "CLI"
