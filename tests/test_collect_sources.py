import json
import pathlib
import types
import urllib.request

import scripts.collect_sources as cs


def fake_response(content: bytes = b"data"):
    class Resp:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return self.data

    return Resp(content)


def test_collect_sources_downloads(monkeypatch, tmp_path):
    vid_dir = tmp_path / "20240101_test"
    vid_dir.mkdir()
    (vid_dir / "sources.txt").write_text("http://example.com/a.html\n")

    monkeypatch.setattr(cs, "VIDEO_ROOT", tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", lambda url: fake_response())

    cs.main()

    dest = vid_dir / "sources" / "1.html"
    assert dest.exists()
    mapping = json.loads((vid_dir / "sources.json").read_text())
    assert mapping["http://example.com/a.html"] == "1.html"


def test_skips_when_no_sources(monkeypatch, tmp_path):
    vid_dir = tmp_path / "20240102_empty"
    vid_dir.mkdir()

    monkeypatch.setattr(cs, "VIDEO_ROOT", tmp_path)
    cs.main()

    assert not (vid_dir / "sources.json").exists()
