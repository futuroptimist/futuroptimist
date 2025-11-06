import json
import pathlib
import runpy
import sys
import tempfile
import warnings

import pytest

import src.scaffold_videos as sv


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
        assert meta["slug"] == "test-title"
        assert meta["transcript_file"] == "subtitles/ABC.srt"


def test_metadata_json_has_trailing_newline(monkeypatch):
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

        meta_path = base / "20240102_test-title" / "metadata.json"
        assert meta_path.read_bytes().endswith(b"\n")


def test_slugify():
    assert sv.slugify("Hello World!") == "hello-world"


def test_fetch_video_info_parses(monkeypatch):
    html = "Title: Example Video\nJan 2, 2024"

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return html.encode()

    resp = Resp()
    monkeypatch.setattr(sv.urllib.request, "urlopen", lambda req: resp)
    title, date = sv.fetch_video_info("abc")
    resp.__enter__()
    resp.__exit__(None, None, None)
    assert title == "Example Video"
    assert date == "20240102"


def test_fetch_video_info_error(monkeypatch):
    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return b"no title here"

    r = Resp()
    monkeypatch.setattr(sv.urllib.request, "urlopen", lambda req: r)
    with pytest.raises(RuntimeError):
        sv.fetch_video_info("abc")
    r.__enter__()
    r.__exit__(None, None, None)


def test_main_exits_without_ids(monkeypatch, tmp_path):
    monkeypatch.setattr(sv, "IDS_FILE", tmp_path / "missing.txt")
    monkeypatch.setattr(sv, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sv, "VIDEO_SCRIPT_ROOT", tmp_path)
    with pytest.raises(SystemExit):
        sv.main()


def test_read_video_ids_ignores_comments(tmp_path, monkeypatch):
    ids = tmp_path / "video_ids.txt"
    ids.write_text("A\n# skip\nB\n")
    monkeypatch.setattr(sv, "IDS_FILE", ids)
    assert sv.read_video_ids() == ["A", "B"]


def test_main_handles_fetch_error(monkeypatch, tmp_path):
    (tmp_path / "video_ids.txt").write_text("BAD\n")
    monkeypatch.setattr(sv, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sv, "IDS_FILE", tmp_path / "video_ids.txt")
    monkeypatch.setattr(sv, "VIDEO_SCRIPT_ROOT", tmp_path)
    monkeypatch.setattr(
        sv, "fetch_video_info", lambda _vid: (_ for _ in ()).throw(RuntimeError("oops"))
    )
    # should not raise despite fetch error
    sv.main()


def test_entrypoint(monkeypatch, tmp_path):
    (tmp_path / "video_ids.txt").write_text("")
    monkeypatch.setattr(sys, "argv", ["scaffold_videos.py"])
    monkeypatch.setattr(sv, "IDS_FILE", tmp_path / "video_ids.txt")
    monkeypatch.setattr(sv, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sv, "VIDEO_SCRIPT_ROOT", tmp_path)

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return b"Title: Dummy\nJan 1, 2024"

    r = Resp()
    monkeypatch.setattr(sv.urllib.request, "urlopen", lambda req: r)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*found in sys.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("src.scaffold_videos", run_name="__main__")
    r.__enter__()
    r.__exit__(None, None, None)
