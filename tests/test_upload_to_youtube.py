from __future__ import annotations

import json
from types import SimpleNamespace

import src.upload_to_youtube as uploader


class DummyInsertRequest:
    def __init__(self, response: dict[str, str]):
        self.response = response

    def execute(self) -> dict[str, str]:
        return self.response


class DummyVideosResource:
    def __init__(self, response: dict[str, str]):
        self.calls: list[tuple[str, dict, object]] = []
        self.response = response

    def insert(self, part: str, body: dict, media_body: object) -> DummyInsertRequest:
        self.calls.append((part, body, media_body))
        return DummyInsertRequest(self.response)


class DummyThumbnailRequest:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def set(self, videoId: str, media_body: object) -> SimpleNamespace:
        self.calls.append((videoId, media_body))

        class _Exec:
            def execute(self_inner) -> dict[str, str]:
                return {"videoId": videoId}

        return _Exec()


class DummyYouTubeService:
    def __init__(self, response: dict[str, str]):
        self.videos_resource = DummyVideosResource(response)
        self.thumbnails_resource = DummyThumbnailRequest()

    def videos(self) -> DummyVideosResource:
        return self.videos_resource

    def thumbnails(self) -> DummyThumbnailRequest:
        return self.thumbnails_resource


def test_upload_video_uses_prepare_payload_and_sets_thumbnail(tmp_path, monkeypatch):
    slug = "20250101_demo"
    repo_root = tmp_path
    (repo_root / "video_scripts" / slug).mkdir(parents=True)
    video_path = repo_root / "dist" / f"{slug}.mp4"
    video_path.parent.mkdir(parents=True)
    video_path.write_bytes(b"video")
    thumbnail = repo_root / "thumb.png"
    thumbnail.write_bytes(b"png")

    payload = {
        "snippet": {"title": "Demo", "description": "", "tags": []},
        "status": {"privacyStatus": "private"},
        "thumbnail_path": str(thumbnail),
    }

    monkeypatch.setattr(
        uploader.prepare_youtube_upload,
        "build_upload_package",
        lambda *a, **k: payload,
    )

    media_calls: list[tuple[str, str, int, bool]] = []

    def fake_media_file_upload(
        path: str, mimetype: str, chunksize: int = -1, resumable: bool = False
    ):
        media_calls.append((path, mimetype, chunksize, resumable))
        return f"MEDIA:{path}"

    monkeypatch.setattr(uploader, "MediaFileUpload", fake_media_file_upload)

    dummy_service = DummyYouTubeService({"id": "video123"})
    monkeypatch.setattr(uploader, "build", lambda *args, **kwargs: dummy_service)
    monkeypatch.setattr(uploader, "load_credentials", lambda *args, **kwargs: object())

    result = uploader.upload_video(
        slug=slug,
        repo_root=repo_root,
        video_path=video_path,
        client_secrets=repo_root / "client.json",
        credentials_path=repo_root / "creds.json",
    )

    assert result["id"] == "video123"
    assert dummy_service.videos_resource.calls[0][0] == "snippet,status"
    assert dummy_service.videos_resource.calls[0][1] == {
        "snippet": payload["snippet"],
        "status": payload["status"],
    }
    assert media_calls[0][0] == str(video_path)
    assert media_calls[0][1] == "video/mp4"
    assert media_calls[0][2] == uploader.UPLOAD_CHUNK_SIZE
    assert media_calls[0][3] is True
    assert dummy_service.thumbnails_resource.calls[0][0] == "video123"
    assert dummy_service.thumbnails_resource.calls[0][1] == f"MEDIA:{thumbnail}"


def test_load_credentials_reuses_cached_token(tmp_path, monkeypatch):
    creds_file = tmp_path / "creds.json"
    creds_file.write_text("{}")
    client_secrets = tmp_path / "client.json"
    client_secrets.write_text("{}")

    fake_creds = SimpleNamespace(valid=True)

    monkeypatch.setattr(
        uploader.Credentials,
        "from_authorized_user_file",
        lambda path, scopes: fake_creds,
    )

    creds = uploader.load_credentials(client_secrets, creds_file)
    assert creds is fake_creds


def test_load_credentials_runs_flow_when_missing(tmp_path, monkeypatch):
    creds_file = tmp_path / "creds.json"
    client_secrets = tmp_path / "client.json"
    client_secrets.write_text(
        json.dumps({"installed": {"client_id": "id", "client_secret": "secret"}})
    )

    class DummyFlow:
        def run_console(self_inner):
            return SimpleNamespace(to_json=lambda: '{"token": 1}', valid=True)

    monkeypatch.setattr(
        uploader.InstalledAppFlow,
        "from_client_secrets_file",
        lambda *args, **kwargs: DummyFlow(),
    )
    monkeypatch.setattr(
        uploader.Credentials,
        "from_authorized_user_file",
        lambda *args, **kwargs: None,
    )

    creds = uploader.load_credentials(client_secrets, creds_file)
    assert creds.valid is True
    assert creds_file.exists()


def test_default_video_path(tmp_path):
    path = uploader._default_video_path("20240101_test", tmp_path)
    assert path == (tmp_path / "dist" / "20240101_test.mp4").resolve()
