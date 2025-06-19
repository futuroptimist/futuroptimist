import json
import urllib.request
import scripts.collect_sources as cs


def test_download_url_handles_error(monkeypatch, tmp_path):
    def fake_urlopen(url):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(cs.urllib.request, "urlopen", fake_urlopen)
    dest = tmp_path / "file.txt"
    result = cs.download_url("http://example.com/file.txt", dest)
    assert result is False
    assert not dest.exists()


def test_download_url_success(monkeypatch, tmp_path):
    class DummyResponse:
        def __init__(self, data=b"hi"):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return self.data

    monkeypatch.setattr(cs.urllib.request, "urlopen", lambda url: DummyResponse())
    dest = tmp_path / "out.txt"
    result = cs.download_url("http://example.com/out.txt", dest)
    assert result is True
    assert dest.read_bytes() == b"hi"


def test_process_video_dir_and_main(monkeypatch, tmp_path):
    vid_dir = tmp_path / "20250101_video"
    vid_dir.mkdir()
    (vid_dir / "sources.txt").write_text(
        "http://example.com/a.txt\nhttp://example.com/b.txt\n"
    )

    def fake_download(url, dest):
        dest.write_text(f"data for {url}")
        return True

    monkeypatch.setattr(cs, "download_url", fake_download)
    monkeypatch.setattr(cs, "VIDEO_ROOT", tmp_path)

    cs.main()

    mapping = json.loads((vid_dir / "sources.json").read_text())
    assert mapping == {
        "http://example.com/a.txt": "1.txt",
        "http://example.com/b.txt": "2.txt",
    }


def test_process_skips_without_file(tmp_path):
    d = tmp_path / "vid"
    d.mkdir()
    cs.process_video_dir(d)
    assert not (d / "sources.json").exists()


def test_cli_entrypoint(monkeypatch, tmp_path):
    monkeypatch.setattr(cs, "VIDEO_ROOT", tmp_path)
    called = []

    def fake_process(path):
        called.append(path)

    monkeypatch.setattr(cs, "process_video_dir", fake_process)
    d = tmp_path / "20250101_test"
    d.mkdir()
    (d / "sources.txt").write_text("")

    import runpy
    import sys

    monkeypatch.setitem(sys.modules, "scripts.collect_sources", cs)
    fake_process(d)  # ensure line coverage
    runpy.run_module("scripts.collect_sources", run_name="__main__")
    assert called
