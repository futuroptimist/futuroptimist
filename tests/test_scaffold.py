import tempfile
import pathlib
import json
import scripts.scaffold_videos as sv


def test_scaffold_creates_files(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        (base / "video_ids.txt").write_text("ABC\n")
        monkeypatch.setattr(sv, "BASE_DIR", base)
        monkeypatch.setattr(sv, "IDS_FILE", base / "video_ids.txt")
        monkeypatch.setattr(sv, "VIDEO_SCRIPT_ROOT", base)

        monkeypatch.setattr(
            sv, "fetch_video_info", lambda vid: ("Test Title", "20240102")
        )

        sv.main()

        vid_dir = base / "20240102_test-title"
        assert vid_dir.is_dir()
        assert (vid_dir / "script.md").exists()
        assert (vid_dir / "footage.md").exists()
        meta = json.loads((vid_dir / "metadata.json").read_text())
        assert meta["youtube_id"] == "ABC"
        assert meta["publish_date"] == "2024-01-02"
