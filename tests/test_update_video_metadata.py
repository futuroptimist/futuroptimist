import json
import runpy
import urllib.error
import urllib.request
import pytest


@pytest.fixture(autouse=True)
def restore_urlopen(monkeypatch):
    original = urllib.request.urlopen
    yield
    monkeypatch.setattr(urllib.request, "urlopen", original)


def test_updates_metadata_from_api(tmp_path, monkeypatch):
    import src.update_video_metadata as updater

    scripts_dir = tmp_path / "video_scripts" / "20240101_demo"
    scripts_dir.mkdir(parents=True)
    meta_path = scripts_dir / "metadata.json"
    meta_path.write_text(
        json.dumps(
            {
                "youtube_id": "abc123",
                "title": "Old Title",
                "publish_date": "2020-01-01",
                "duration_seconds": 0,
                "keywords": [],
                "description": "",
            },
            indent=2,
        )
        + "\n"
    )

    monkeypatch.setenv("YOUTUBE_API_KEY", "TEST")
    monkeypatch.setattr(updater, "BASE_DIR", tmp_path)
    monkeypatch.setattr(updater, "VIDEO_ROOT", tmp_path / "video_scripts")

    class FakeResponse:
        def __init__(self, data: bytes):
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    payload = {
        "items": [
            {
                "snippet": {
                    "title": "New Title",
                    "publishedAt": "2024-08-15T12:34:56Z",
                    "description": "Updated description",
                    "tags": ["space", "maker"],
                    "thumbnails": {
                        "maxres": {"url": "https://img.youtube.com/maxres.jpg"},
                        "high": {"url": "https://img.youtube.com/high.jpg"},
                    },
                },
                "contentDetails": {"duration": "PT1H2M3S"},
                "statistics": {"viewCount": "12345"},
            }
        ]
    }

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda url, timeout=10: FakeResponse(json.dumps(payload).encode("utf-8")),
    )

    updater.main([])

    data = json.loads(meta_path.read_text())
    assert data["title"] == "New Title"
    assert data["publish_date"] == "2024-08-15"
    assert data["duration_seconds"] == 3723
    assert data["keywords"] == ["space", "maker"]
    assert data["description"] == "Updated description"
    assert data["thumbnail"] == "https://img.youtube.com/maxres.jpg"
    assert data["view_count"] == 12345


def test_parse_duration_handles_weeks():
    import src.update_video_metadata as updater

    assert updater.parse_duration("PT5M") == 300
    assert updater.parse_duration("P1DT1H") == 90000
    assert updater.parse_duration("P1W") == 604800
    assert updater.parse_duration("invalid") == 0


def test_fetch_metadata_thumbnail_fallback(monkeypatch):
    import src.update_video_metadata as updater

    payload = {
        "items": [
            {
                "snippet": {
                    "title": "Fallback",
                    "publishedAt": "",
                    "description": "",
                    "tags": [],
                    "thumbnails": {
                        "high": {"url": "https://img.youtube.com/high.jpg"},
                        "default": {"url": "https://img.youtube.com/default.jpg"},
                    },
                },
                "contentDetails": {"duration": "PT0S"},
                "statistics": {},
            }
        ]
    }

    class FakeResponse:
        def __init__(self, data: bytes):
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda url, timeout=10: FakeResponse(json.dumps(payload).encode("utf-8")),
    )

    info = updater.fetch_metadata("fallback", "TOKEN")
    assert info["thumbnail"] == "https://img.youtube.com/high.jpg"
    assert info["view_count"] is None


def test_entrypoint_runs(monkeypatch, tmp_path):
    import src.update_video_metadata  # noqa: F401

    import src.update_video_metadata as updater

    monkeypatch.setattr(updater, "BASE_DIR", tmp_path)
    monkeypatch.setattr(updater, "VIDEO_ROOT", tmp_path / "video_scripts")
    (tmp_path / "video_scripts").mkdir()
    monkeypatch.setenv("YOUTUBE_API_KEY", "TEST")

    class Boom(urllib.error.URLError):
        pass

    def failing_urlopen(url, timeout=10):
        raise Boom("fail")

    monkeypatch.setattr(urllib.request, "urlopen", failing_urlopen)

    with pytest.raises(SystemExit):
        runpy.run_module("src.update_video_metadata", run_name="__main__")


def test_main_returns_error_on_partial_failures(monkeypatch, tmp_path):
    import src.update_video_metadata as updater

    scripts_dir = tmp_path / "video_scripts"
    scripts_dir.mkdir()

    first = scripts_dir / "20240101_demo" / "metadata.json"
    first.parent.mkdir()
    first.write_text(
        json.dumps(
            {
                "youtube_id": "good",
                "title": "Old Title",
                "publish_date": "2020-01-01",
                "duration_seconds": 0,
                "keywords": [],
                "description": "",
            },
            indent=2,
        )
        + "\n"
    )

    second = scripts_dir / "20240102_demo" / "metadata.json"
    second.parent.mkdir()
    second.write_text(
        json.dumps(
            {
                "youtube_id": "bad",
                "title": "Keep Title",
                "publish_date": "2020-01-02",
                "duration_seconds": 0,
                "keywords": [],
                "description": "",
            },
            indent=2,
        )
        + "\n"
    )

    monkeypatch.setenv("YOUTUBE_API_KEY", "TEST")
    monkeypatch.setattr(updater, "BASE_DIR", tmp_path)
    monkeypatch.setattr(updater, "VIDEO_ROOT", scripts_dir)

    responses = [
        {
            "title": "New Title",
            "publish_date": "2024-08-15",
            "duration_seconds": 10,
            "description": "Updated",
            "keywords": ["tag"],
            "thumbnail": "https://img.youtube.com/fallback.jpg",
        },
        None,
    ]

    def fake_fetch(video_id, youtube_key, timeout=10):  # noqa: ARG001
        return responses.pop(0)

    monkeypatch.setattr(updater, "fetch_metadata", fake_fetch)

    exit_code = updater.main([])

    assert exit_code == 1
    first_data = json.loads(first.read_text())
    assert first_data["title"] == "New Title"
    assert first_data["publish_date"] == "2024-08-15"
    assert first_data["duration_seconds"] == 10
    assert first_data["keywords"] == ["tag"]
    assert json.loads(second.read_text())["title"] == "Keep Title"
