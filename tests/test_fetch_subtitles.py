import builtins
import types
import scripts.fetch_subtitles as fs
import subprocess


def test_read_video_ids(tmp_path, monkeypatch):
    # Prepare a temporary IDs file
    ids_file = tmp_path / "video_ids.txt"
    ids_file.write_text("A\nB\n  \nC\n")

    monkeypatch.setattr(fs, "IDS_FILE", ids_file)
    result = fs.read_video_ids()
    assert result == ["A", "B", "C"]


def test_download_subtitles_constructs_command(monkeypatch):
    captured = {}

    def fake_run(cmd, check):
        captured['cmd'] = cmd
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    monkeypatch.setattr(fs, "OUTPUT_DIR", fs.OUTPUT_DIR)  # ensure exists
    fs.download_subtitles("XYZ123")

    # Validate that the command includes the video ID and key flags
    cmd = " ".join(captured['cmd'])
    assert "https://www.youtube.com/watch?v=XYZ123" in cmd
    assert "--skip-download" in cmd
    assert "--write-sub" in cmd
