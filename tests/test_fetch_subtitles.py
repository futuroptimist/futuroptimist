import types
import scripts.fetch_subtitles as fs
import subprocess
import pytest
import shutil


def test_read_video_ids(tmp_path, monkeypatch):
    ids_file = tmp_path / "video_ids.txt"
    ids_file.write_text("A\nB\n  \nC\n")
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


def test_entrypoint(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _: "yt-dlp")
    monkeypatch.setattr(fs, "IDS_FILE", tmp_path / "ids.txt")
    monkeypatch.setattr(fs, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(fs, "read_video_ids", lambda: [])
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    import runpy

    runpy.run_module("scripts.fetch_subtitles", run_name="__main__")
