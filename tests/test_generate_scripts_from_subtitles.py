from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import generate_scripts_from_subtitles as gss


@pytest.fixture
def repo_structure(tmp_path: Path) -> Path:
    repo = tmp_path
    video_dir = repo / "video_scripts" / "20240101_demo"
    video_dir.mkdir(parents=True)
    metadata = {
        "youtube_id": "abc123",
        "title": "Demo Title",
        "publish_date": "2024-01-01",
        "duration_seconds": 0,
        "status": "draft",
        "description": "",
    }
    (video_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    subs = repo / "subtitles"
    subs.mkdir()
    (subs / "abc123.srt").write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nHello world!\n\n"
    )
    return repo


def test_generate_scripts_from_subtitles_creates_markdown(repo_structure: Path) -> None:
    repo = repo_structure
    result = gss.generate_scripts(
        video_root=repo / "video_scripts",
        subtitles_root=repo / "subtitles",
        force=False,
    )
    script_path = repo / "video_scripts" / "20240101_demo" / "script.md"
    assert script_path.exists()
    content = script_path.read_text()
    assert "# Demo Title" in content
    assert "[NARRATOR]: Hello world!" in content
    assert result["written"] == [script_path]


def test_generate_scripts_from_subtitles_skips_existing(repo_structure: Path) -> None:
    repo = repo_structure
    script_path = repo / "video_scripts" / "20240101_demo" / "script.md"
    script_path.write_text("Existing content\n")
    result = gss.generate_scripts(
        video_root=repo / "video_scripts",
        subtitles_root=repo / "subtitles",
        force=False,
    )
    assert script_path.read_text() == "Existing content\n"
    assert result["written"] == []
    assert result["skipped"] == [script_path]
