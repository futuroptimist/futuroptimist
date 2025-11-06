from __future__ import annotations

import json
import pathlib
from collections.abc import Sequence

import pytest


def _setup_converted(
    tmp_path: pathlib.Path, slug: str, names: Sequence[str]
) -> pathlib.Path:
    root = tmp_path / "footage" / slug / "converted"
    root.mkdir(parents=True)
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"data")
    return root


def test_discover_clips_returns_sorted_mp4(tmp_path: pathlib.Path) -> None:
    from src import render_video

    converted = _setup_converted(
        tmp_path, "20250101_demo", ["c.mp4", "a.mp4", "b.mov", "nested/d.mp4"]
    )
    clips = render_video.discover_clips(converted)
    assert [clip.name for clip in clips] == ["a.mp4", "c.mp4", "d.mp4"]


def test_render_slug_invokes_ffmpeg_with_concat(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src import render_video

    converted = _setup_converted(tmp_path, "20250101_demo", ["a.mp4", "b.mp4"])
    output_dir = tmp_path / "dist"

    commands: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool) -> None:
        commands.append(cmd)
        list_path = pathlib.Path(cmd[7])
        lines = list_path.read_text(encoding="utf-8").splitlines()
        assert lines == [
            f"file '{(converted / 'a.mp4').resolve().as_posix()}'",
            f"file '{(converted / 'b.mp4').resolve().as_posix()}'",
        ]

    monkeypatch.setattr(render_video.subprocess, "run", fake_run)

    result = render_video.render_slug(
        "20250101_demo",
        footage_root=tmp_path / "footage",
        output_dir=output_dir,
        captions=None,
        dry_run=False,
    )

    assert result == output_dir / "20250101_demo.mp4"
    assert commands and commands[0][0] == "ffmpeg"
    assert commands[0][-1] == str(result)


def test_resolve_captions_prefers_metadata_transcript(tmp_path: pathlib.Path) -> None:
    from src import render_video

    repo_root = tmp_path
    video_dir = repo_root / "video_scripts" / "20250101_demo"
    video_dir.mkdir(parents=True)
    transcript_rel = pathlib.Path("subtitles/custom.srt")
    (repo_root / transcript_rel).parent.mkdir(parents=True)
    (repo_root / transcript_rel).write_text("data", encoding="utf-8")
    metadata = {
        "youtube_id": "abc123",
        "transcript_file": transcript_rel.as_posix(),
    }
    (video_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    resolved = render_video.resolve_captions("20250101_demo", repo_root, None)
    assert resolved == (repo_root / transcript_rel)


def test_main_dry_run_skips_ffmpeg(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from src import render_video

    _setup_converted(tmp_path, "20250101_demo", ["clip.mp4"])

    called = False

    def boom(cmd: list[str], check: bool) -> None:  # pragma: no cover - guard
        nonlocal called
        called = True

    monkeypatch.setattr(render_video.subprocess, "run", boom)

    exit_code = render_video.main(
        [
            "--slug",
            "20250101_demo",
            "--footage-root",
            str(tmp_path / "footage"),
            "--output-dir",
            str(tmp_path / "dist"),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert called is False
    captured = capsys.readouterr()
    assert "Dry run" in captured.out


def test_render_slug_raises_without_clips(tmp_path: pathlib.Path) -> None:
    from src import render_video

    (tmp_path / "footage" / "20250101_demo" / "converted").mkdir(parents=True)
    with pytest.raises(ValueError):
        render_video.render_slug(
            "20250101_demo",
            footage_root=tmp_path / "footage",
            output_dir=tmp_path / "dist",
        )
