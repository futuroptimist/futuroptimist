from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.annotate_publish as ap


def _write_metadata(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_annotate_metadata_derives_url_and_duration(tmp_path: Path) -> None:
    meta_path = tmp_path / "metadata.json"
    _write_metadata(
        meta_path,
        {
            "youtube_id": "abc123",
            "title": "Sample",
            "status": "live",
        },
    )

    changed = ap.annotate_metadata(
        meta_path,
        processing_started_at="2025-10-20T12:00:00Z",
        processing_completed_at="2025-10-20T12:10:30Z",
    )

    assert changed is True
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert payload["video_url"] == "https://youtu.be/abc123"
    assert payload["processing"]["started_at"] == "2025-10-20T12:00:00+00:00"
    assert payload["processing"]["completed_at"] == "2025-10-20T12:10:30+00:00"
    assert payload["processing"]["duration_seconds"] == 630


def test_main_updates_selected_slugs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path
    video_root = repo / "video_scripts"
    slug_dir = video_root / "20250101_future"
    slug_dir.mkdir(parents=True)
    other_dir = video_root / "20240101_old"
    other_dir.mkdir(parents=True)
    _write_metadata(
        slug_dir / "metadata.json",
        {
            "youtube_id": "fresh456",
            "title": "Future Video",
            "status": "live",
        },
    )
    _write_metadata(
        other_dir / "metadata.json",
        {
            "youtube_id": "other999",
            "title": "Other",
            "status": "live",
        },
    )

    exit_code = ap.main(
        [
            "--slug",
            "20250101_future",
            "--video-root",
            str(video_root),
            "--processing-seconds",
            "42",
        ]
    )

    assert exit_code == 0
    updated = json.loads((slug_dir / "metadata.json").read_text(encoding="utf-8"))
    untouched = json.loads((other_dir / "metadata.json").read_text(encoding="utf-8"))
    assert updated["video_url"] == "https://youtu.be/fresh456"
    assert updated["processing"]["duration_seconds"] == 42
    assert "processing" not in untouched
    assert "video_url" not in untouched

    output = capsys.readouterr().out
    assert "Updated 1 metadata file" in output
