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
