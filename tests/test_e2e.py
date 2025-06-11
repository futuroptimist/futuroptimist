import json, pathlib, tempfile, types
import scripts.scaffold_videos as scaffold
import scripts.fetch_subtitles as fs
import subprocess


def test_e2e_pipeline(monkeypatch):
    """Simulate full journey: scaffold -> fetch subtitles (mocked)."""
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        # 1. Create video_ids.txt
        vid = "XYZ123"
        (base / "video_ids.txt").write_text(f"{vid}\n")

        # Monkeypatch base paths for both modules
        monkeypatch.setattr(scaffold, "BASE_DIR", base)
        monkeypatch.setattr(scaffold, "IDS_FILE", base / "video_ids.txt")
        monkeypatch.setattr(scaffold, "VIDEO_SCRIPT_ROOT", base)
        monkeypatch.setattr(
            scaffold, "fetch_video_info", lambda vid: ("Video", "20240202")
        )

        # 1a. Scaffold
        scaffold.main()
        vdir = base / "20240202_video"
        assert vdir.exists(), "Video directory created"
        assert (vdir / "script.md").exists()
        meta_data = json.loads((vdir / "metadata.json").read_text())
        assert meta_data["youtube_id"] == vid
        assert meta_data["publish_date"] == "2024-02-02"

        # 2. Fetch subtitles mocked
        calls = []

        def fake_run(cmd, check=True):
            # Simulate first attempt failing (conversion error) then success
            calls.append(cmd)
            if len(calls) == 1:
                raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
            return types.SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(fs, "BASE_DIR", base)
        monkeypatch.setattr(fs, "IDS_FILE", base / "video_ids.txt")
        monkeypatch.setattr(fs, "OUTPUT_DIR", base / "subtitles")
        monkeypatch.setattr(fs, "ensure_requirements", lambda: None)

        fs.main()  # will iterate & call download_subtitles once

        # We expect two subprocess calls (primary + fallback)
        assert len(calls) == 2
        # verify fallback without --convert-subs
        assert "--convert-subs" not in calls[1]
