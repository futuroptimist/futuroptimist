import json
import pathlib
import urllib.request
import src.collect_sources as cs


def test_download_url_handles_error(monkeypatch, tmp_path):
    seen = {}

    def fake_urlopen(req, *, timeout=None):
        seen["ua"] = req.get_header("User-agent")
        seen["timeout"] = timeout
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(cs.urllib.request, "urlopen", fake_urlopen)
    dest = tmp_path / "file.txt"
    result = cs.download_url("http://example.com/file.txt", dest)
    assert result is False
    assert not dest.exists()
    assert seen["ua"] == cs.USER_AGENT
    assert seen["timeout"] == cs.URL_TIMEOUT


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

    def fake_urlopen(req, *, timeout=None):
        assert timeout == cs.URL_TIMEOUT
        assert req.get_header("User-agent") == cs.USER_AGENT
        return DummyResponse()

    monkeypatch.setattr(cs.urllib.request, "urlopen", fake_urlopen)
    dest = tmp_path / "out.txt"
    result = cs.download_url("http://example.com/out.txt", dest)
    assert result is True
    assert dest.read_bytes() == b"hi"


def test_download_url_write_error(monkeypatch, tmp_path):
    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return b"data"

    def fake_urlopen(req, *, timeout=None):
        return DummyResponse()

    dest = tmp_path / "out.txt"

    def fail_write(self, _data):
        raise OSError("disk full")

    monkeypatch.setattr(cs.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(pathlib.Path, "write_bytes", fail_write)
    result = cs.download_url("http://example.com/out.txt", dest)
    assert result is False
    assert not dest.exists()


def test_process_video_dir_and_main(monkeypatch, tmp_path):
    vid_dir = tmp_path / "20250101_video"
    vid_dir.mkdir()
    (vid_dir / "sources.txt").write_text(
        "http://example.com/a.txt\nhttp://example.com/b.txt\n"
    )

    urls_file = tmp_path / "source_urls.txt"
    urls_file.write_text("http://example.com/global.txt\n")

    def fake_download(url, dest):
        dest.write_text(f"data for {url}")
        return True

    monkeypatch.setattr(cs, "download_url", fake_download)
    monkeypatch.setattr(cs, "VIDEO_ROOT", tmp_path)
    global_dir = tmp_path / "sources"
    monkeypatch.setenv(cs.SOURCE_URLS_ENV, str(urls_file))
    monkeypatch.setenv(cs.GLOBAL_SOURCES_ENV, str(global_dir))

    cs.main()

    mapping = json.loads((vid_dir / "sources.json").read_text())
    assert mapping == {
        "http://example.com/a.txt": "1.txt",
        "http://example.com/b.txt": "2.txt",
    }

    global_mapping = json.loads((global_dir / "sources.json").read_text())
    assert global_mapping == {"http://example.com/global.txt": "1.txt"}
    assert (global_dir / "sources.json").read_text().endswith("\n")


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
    monkeypatch.setenv(cs.SOURCE_URLS_ENV, str(tmp_path / "source_urls.txt"))
    monkeypatch.setenv(cs.GLOBAL_SOURCES_ENV, str(tmp_path / "sources"))
    monkeypatch.setattr(cs, "download_url", lambda url, dest: False)
    d = tmp_path / "20250101_test"
    d.mkdir()
    (d / "sources.txt").write_text("")

    import runpy
    import sys
    import warnings

    monkeypatch.setitem(sys.modules, "src.collect_sources", cs)
    fake_process(d)  # ensure line coverage
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*found in sys.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("src.collect_sources", run_name="__main__")
    assert called


def test_sources_json_has_trailing_newline(monkeypatch, tmp_path):
    vid_dir = tmp_path / "20250101_newline"
    vid_dir.mkdir()
    (vid_dir / "sources.txt").write_text("http://example.com/a.txt\n")

    def fake_download(url, dest):
        dest.write_text("data")
        return True

    monkeypatch.setattr(cs, "download_url", fake_download)
    cs.process_video_dir(vid_dir)

    content = (vid_dir / "sources.json").read_text()
    assert content.endswith("\n")


def test_process_global_sources(monkeypatch, tmp_path):
    urls_file = tmp_path / "source_urls.txt"
    urls_file.write_text(
        "# comment\n\nhttp://example.com/a.txt\nhttp://example.com/path/data.mp4\n"
    )

    written: dict[str, pathlib.Path] = {}

    def fake_download(url, dest):
        dest.write_text("data")
        written[url] = dest
        return True

    monkeypatch.setattr(cs, "download_url", fake_download)
    global_dir = tmp_path / "sources"

    mapping = cs.process_global_sources(source_file=urls_file, dest_dir=global_dir)

    assert mapping == {
        "http://example.com/a.txt": "1.txt",
        "http://example.com/path/data.mp4": "2.mp4",
    }
    assert written["http://example.com/a.txt"].name == "1.txt"
    assert written["http://example.com/path/data.mp4"].name == "2.mp4"
    output_path = global_dir / "sources.json"
    assert json.loads(output_path.read_text()) == mapping
    assert output_path.read_text().endswith("\n")
