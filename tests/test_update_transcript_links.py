import json
import scripts.update_transcript_links as utl


def test_update_transcript_links(tmp_path, monkeypatch):
    base = tmp_path
    subs = base / "subtitles"
    subs.mkdir()
    scripts_dir = base / "scripts"
    scripts_dir.mkdir()
    meta = scripts_dir / "20240101_test" / "metadata.json"
    meta.parent.mkdir()
    meta.write_text(json.dumps({"youtube_id": "ABC", "title": "t"}))
    (subs / "ABC.srt").write_text("hi")

    monkeypatch.setattr(utl, "BASE_DIR", base)
    monkeypatch.setattr(utl, "SCRIPT_ROOT", scripts_dir)
    monkeypatch.setattr(utl, "SUBS_DIR", subs)

    utl.main()

    data = json.loads(meta.read_text())
    assert data["transcript_file"] == "subtitles/ABC.srt"


def test_fetch_from_api_when_missing(tmp_path, monkeypatch):
    base = tmp_path
    scripts_dir = base / "scripts"
    scripts_dir.mkdir()
    meta = scripts_dir / "20240101_test" / "metadata.json"
    meta.parent.mkdir()
    meta.write_text(json.dumps({"youtube_id": "ABC", "title": "t"}))

    monkeypatch.setattr(utl, "BASE_DIR", base)
    monkeypatch.setattr(utl, "SCRIPT_ROOT", scripts_dir)
    monkeypatch.setattr(utl, "SUBS_DIR", base / "subtitles")
    monkeypatch.setattr(utl, "API_KEY", "X")

    class Resp:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return self.data

    def fake_urlopen(url):
        if "captions?" in url:
            listing = {"items": [{"id": "1", "snippet": {"language": "en"}}]}
            return Resp(json.dumps(listing).encode())
        elif "captions/1" in url:
            return Resp(b"foo")
        raise AssertionError(url)

    monkeypatch.setattr(utl.urllib.request, "urlopen", fake_urlopen)

    utl.main()

    out = base / "subtitles" / "ABC.srt"
    assert out.exists()
    data = json.loads(meta.read_text())
    assert data["transcript_file"] == "subtitles/ABC.srt"
