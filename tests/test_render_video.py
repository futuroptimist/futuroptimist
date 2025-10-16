from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import render_video
from src.render_video import RenderError


def _stub_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(render_video.shutil, "which", lambda _: "/usr/bin/ffmpeg")


def _stub_repo_paths(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(render_video, "REPO_ROOT", root)


def test_render_video_concatenates_segments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_repo_paths(monkeypatch, tmp_path)
    _stub_ffmpeg(monkeypatch)

    slug = "20250101_demo"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)
    clip_a = converted / "a.mp4"
    clip_b = converted / "b.mp4"
    clip_a.write_bytes(b"a")
    clip_b.write_bytes(b"b")

    video_root = tmp_path / "video_scripts"
    dist_root = tmp_path / "dist"

    captured: dict[str, object] = {}

    def fake_build_ffmpeg_command(**kwargs):
        captured["inputs"] = list(kwargs["inputs"])
        captured["concat_lines"] = (
            kwargs["concat_file"].read_text(encoding="utf-8").splitlines()
        )
        captured["output"] = kwargs["output"]
        captured["captions"] = kwargs["captions"]
        return ["ffmpeg", "-i", str(kwargs["concat_file"]), str(kwargs["output"])]

    monkeypatch.setattr(
        render_video, "_build_ffmpeg_command", fake_build_ffmpeg_command
    )

    commands: list[list[str]] = []

    def fake_run(cmd, check):  # noqa: ANN001
        commands.append(list(cmd))

    monkeypatch.setattr(render_video.subprocess, "run", fake_run)

    result = render_video.render_video(
        slug,
        footage_root=footage_root,
        video_root=video_root,
        dist_root=dist_root,
        overwrite=True,
    )

    expected_output = dist_root / f"{slug}.mp4"
    assert result == expected_output
    assert captured["inputs"] == [clip_a.resolve(), clip_b.resolve()]
    assert captured["concat_lines"] == [
        f"file '{clip_a.resolve()}'",
        f"file '{clip_b.resolve()}'",
    ]
    assert captured["captions"] is None
    assert commands and commands[0][-1] == str(expected_output)


def test_render_video_respects_selects_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_repo_paths(monkeypatch, tmp_path)
    _stub_ffmpeg(monkeypatch)

    slug = "20251212_demo"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)
    clip_a = converted / "alpha.mp4"
    clip_b = converted / "beta.mp4"
    clip_c = converted / "gamma.mp4"
    clip_a.write_bytes(b"a")
    clip_b.write_bytes(b"b")
    clip_c.write_bytes(b"c")

    selects = tmp_path / "selects.txt"
    selects.write_text(
        "\n".join(
            [
                "converted\\\\beta.mp4",
                "converted/alpha.mp4",
                "converted\\\\alpha.mp4",  # duplicate, should be ignored
                "converted/not-video.wav",
            ]
        ),
        encoding="utf-8",
    )

    video_root = tmp_path / "video_scripts"
    dist_root = tmp_path / "dist"

    captured_inputs: list[Path] = []

    def fake_build_ffmpeg_command(**kwargs):
        captured_inputs.extend(kwargs["inputs"])
        return ["ffmpeg", "-i", str(kwargs["concat_file"]), str(kwargs["output"])]

    monkeypatch.setattr(
        render_video, "_build_ffmpeg_command", fake_build_ffmpeg_command
    )
    monkeypatch.setattr(
        render_video.subprocess, "run", lambda *args, **kwargs: None
    )  # noqa: ARG005

    render_video.render_video(
        slug,
        footage_root=footage_root,
        video_root=video_root,
        dist_root=dist_root,
        selects_file=selects,
        overwrite=True,
    )

    assert captured_inputs == [clip_b.resolve(), clip_a.resolve()]


def test_render_video_infers_captions_from_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_repo_paths(monkeypatch, tmp_path)
    _stub_ffmpeg(monkeypatch)

    slug = "20260101_story"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)
    (converted / "clip.mp4").write_bytes(b"x")

    video_root = tmp_path / "video_scripts"
    slug_dir = video_root / slug
    slug_dir.mkdir(parents=True)
    captions_file = slug_dir / "captions.srt"
    captions_file.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8"
    )
    metadata = {"transcript_file": "captions.srt"}
    (slug_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    dist_root = tmp_path / "dist"

    captured: dict[str, object] = {}

    def fake_build_ffmpeg_command(**kwargs):
        captured["captions"] = kwargs["captions"]
        return ["ffmpeg", "-i", str(kwargs["concat_file"]), str(kwargs["output"])]

    monkeypatch.setattr(
        render_video, "_build_ffmpeg_command", fake_build_ffmpeg_command
    )
    monkeypatch.setattr(
        render_video.subprocess, "run", lambda *args, **kwargs: None
    )  # noqa: ARG005

    render_video.render_video(
        slug,
        footage_root=footage_root,
        video_root=video_root,
        dist_root=dist_root,
        overwrite=True,
    )

    assert captured["captions"] == captions_file.resolve()


def test_render_video_dry_run_prints_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_repo_paths(monkeypatch, tmp_path)
    _stub_ffmpeg(monkeypatch)

    slug = "20260909_plan"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)
    clip = converted / "segment.mp4"
    clip.write_bytes(b"x")

    video_root = tmp_path / "video_scripts"
    dist_root = tmp_path / "dist"

    def fake_build_ffmpeg_command(**kwargs):
        return [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(kwargs["concat_file"]),
            "-vf",
            "subtitles=/tmp/captions.srt",
            str(kwargs["output"]),
        ]

    monkeypatch.setattr(
        render_video, "_build_ffmpeg_command", fake_build_ffmpeg_command
    )
    monkeypatch.setattr(
        render_video.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ffmpeg should not run")
        ),
    )

    render_video.render_video(
        slug,
        footage_root=footage_root,
        video_root=video_root,
        dist_root=dist_root,
        dry_run=True,
    )

    out = capsys.readouterr().out.strip().splitlines()
    assert any(line.startswith("ffmpeg -f concat") for line in out)
    assert any("Dry run: would write" in line for line in out)


def test_render_video_errors_without_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_repo_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(render_video.shutil, "which", lambda _: None)

    with pytest.raises(RenderError, match="ffmpeg executable not found"):
        render_video.render_video(
            "20261010_missing",
            footage_root=tmp_path / "footage",
            video_root=tmp_path / "video_scripts",
            dist_root=tmp_path / "dist",
        )


def test_render_video_errors_when_no_clips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_repo_paths(monkeypatch, tmp_path)
    _stub_ffmpeg(monkeypatch)

    slug = "20261111_empty"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    converted.mkdir(parents=True)

    with pytest.raises(RenderError, match="No converted MP4 clips"):
        render_video.render_video(
            slug,
            footage_root=footage_root,
            video_root=tmp_path / "video_scripts",
            dist_root=tmp_path / "dist",
        )
