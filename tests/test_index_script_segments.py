import json
from pathlib import Path

import pytest

import src.index_script_segments as segments


def _write_script(slug_dir: Path, *, lines: list[str]) -> None:
    slug_dir.mkdir(parents=True, exist_ok=True)
    script = slug_dir / "script.md"
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture()
def demo_video(tmp_path: Path) -> Path:
    video_root = tmp_path / "video_scripts"
    slug_dir = video_root / "20240101_demo"
    meta = {
        "youtube_id": "ABC123",
        "title": "Demo Video",
        "publish_date": "2024-01-01",
    }
    slug_dir.mkdir(parents=True, exist_ok=True)
    (slug_dir / "metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    _write_script(
        slug_dir,
        lines=[
            "# Demo Video",
            "",
            "> Draft script for video `ABC123`",
            "",
            "## Script",
            "",
            "[NARRATOR]: Hello world!  <!-- 00:00:00,000 -> 00:00:02,000 -->",
            "",
            "[VISUAL]: Show intro montage",
            "",
            "[NARRATOR]: Second beat without timing",
        ],
    )
    return video_root


def test_build_index_collects_segments(tmp_path: Path, demo_video: Path) -> None:
    output = tmp_path / "segments.json"
    data = segments.build_index(video_root=demo_video, output_path=output)
    assert output.exists(), "Index should be written to the requested path"
    assert data == json.loads(output.read_text(encoding="utf-8"))
    assert len(data) == 2

    first, second = data
    assert first["slug"] == "20240101_demo"
    assert first["segment"] == 1
    assert first["text"] == "Hello world!"
    assert first["start"] == "00:00:00,000"
    assert first["end"] == "00:00:02,000"
    assert first["youtube_id"] == "ABC123"
    assert first["title"] == "Demo Video"
    assert first["publish_date"] == "2024-01-01"

    assert second["segment"] == 2
    assert second["text"] == "Second beat without timing"
    assert second["start"] is None
    assert second["end"] is None


def test_main_returns_zero(tmp_path: Path, demo_video: Path) -> None:
    output = tmp_path / "out.json"
    exit_code = segments.main(
        ["--video-root", str(demo_video), "--output", str(output)]
    )
    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 2
