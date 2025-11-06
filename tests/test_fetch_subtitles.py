import shutil
import subprocess
import types

import pytest

import src.fetch_subtitles as fs


def test_read_video_ids(tmp_path, monkeypatch):
    ids_file = tmp_path / "video_ids.txt"
    ids_file.write_text("A\n# comment\nB\n  \nC\n")
    monkeypatch.setattr(fs, "IDS_FILE", ids_file)
    result = fs.read_video_ids()
    assert result == ["A", "B", "C"]


def test_download_subtitles_constructs_command(monkeypatch):
    captured = {}

    def fake_run(cmd, check):
        captured["cmd"] = cmd
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(fs, "OUTPUT_DIR", fs.OUTPUT_DIR)
    fs.download_subtitles("XYZ123")

    cmd = " ".join(captured["cmd"])
    assert "https://www.youtube.com/watch?v=XYZ123" in cmd
    assert "--skip-download" in cmd
    assert "--write-sub" in cmd
    assert "--write-auto-sub" not in cmd


def test_download_subtitles_fallback_converts_vtt(tmp_path, monkeypatch):
    out_dir = tmp_path / "subs"
    out_dir.mkdir()
    monkeypatch.setattr(fs, "OUTPUT_DIR", out_dir)

    calls: list[list[str]] = []

    def fake_run(cmd, check):
        calls.append(cmd)
        if len(calls) == 1:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
        vtt_path = out_dir / "XYZ123.en.vtt"
        vtt_path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello world!\n")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    fs.download_subtitles("XYZ123")

    srt_path = out_dir / "XYZ123.srt"
    assert srt_path.exists()
    text = srt_path.read_text().strip().splitlines()
    assert text[0] == "1"
    assert text[1] == "00:00:00,000 --> 00:00:02,000"
    assert text[2] == "Hello world!"
    assert not any(p.suffix == ".vtt" for p in out_dir.iterdir())


def test_ensure_requirements_missing(monkeypatch):
    monkeypatch.setattr(fs.shutil, "which", lambda _: None)
    with pytest.raises(SystemExit):
        fs.ensure_requirements()


def test_main_invokes_download(monkeypatch, tmp_path):
    ids_file = tmp_path / "video_ids.txt"
    ids_file.write_text("A\nB\n")
    monkeypatch.setattr(fs, "IDS_FILE", ids_file)
    out_dir = tmp_path / "subs"
    monkeypatch.setattr(fs, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(fs, "ensure_requirements", lambda: None)
    calls = []

    def fake_download(vid):
        calls.append(vid)

    monkeypatch.setattr(fs, "download_subtitles", fake_download)
    fs.main()
    assert out_dir.exists()
    assert calls == ["A", "B"]


def test_read_video_ids_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(fs, "IDS_FILE", tmp_path / "none.txt")
    with pytest.raises(SystemExit):
        fs.read_video_ids()


def test_main_handles_failure(monkeypatch, tmp_path):
    ids_file = tmp_path / "ids.txt"
    ids_file.write_text("A\n")
    monkeypatch.setattr(fs, "IDS_FILE", ids_file)
    monkeypatch.setattr(fs, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(fs, "ensure_requirements", lambda: None)

    def fail_download(_):
        raise subprocess.CalledProcessError(returncode=1, cmd=["yt-dlp"])

    monkeypatch.setattr(fs, "download_subtitles", fail_download)
    fs.main()


def test_entrypoint(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _: "yt-dlp")
    monkeypatch.setattr(fs, "IDS_FILE", tmp_path / "ids.txt")
    monkeypatch.setattr(fs, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(fs, "read_video_ids", lambda: [])
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    import runpy
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*found in sys.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("src.fetch_subtitles", run_name="__main__")
