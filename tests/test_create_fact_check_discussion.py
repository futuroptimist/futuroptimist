import json
import pathlib
import pytest

import src.create_fact_check_discussion as cfcd


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def _write_metadata(tmp_path: pathlib.Path, slug: str, data: dict) -> pathlib.Path:
    script_dir = tmp_path / slug
    script_dir.mkdir(parents=True)
    meta_path = script_dir / "metadata.json"
    meta_path.write_text(json.dumps(data), encoding="utf-8")
    return meta_path


def test_main_creates_discussion(tmp_path, monkeypatch, capsys):
    slug = "20240101_test-video"
    _write_metadata(
        tmp_path,
        slug,
        {
            "title": "Test Video",
            "youtube_id": "abc123",
            "description": "A draft ready for fact-checking.",
        },
    )

    captured_requests = []
    responses = [
        DummyResponse(
            {
                "data": {
                    "repository": {
                        "id": "repo123",
                        "discussionCategories": {
                            "nodes": [
                                {"id": "cat456", "name": "Fact Checks"},
                                {"id": "cat789", "name": "Ideas"},
                            ]
                        },
                    }
                }
            }
        ),
        DummyResponse(
            {
                "data": {
                    "createDiscussion": {
                        "discussion": {
                            "url": "https://github.com/futuroptimist/futuroptimist/discussions/42"
                        }
                    }
                }
            }
        ),
    ]

    def fake_urlopen(request):
        captured_requests.append(request)
        assert responses, "Unexpected GraphQL call"
        return responses.pop(0)

    monkeypatch.setattr(cfcd.github_auth, "get_github_token", lambda: "token-123")
    monkeypatch.setattr(cfcd.urllib.request, "urlopen", fake_urlopen)

    exit_code = cfcd.main(
        [
            slug,
            "--video-root",
            str(tmp_path),
            "--category",
            "Fact Checks",
            "--repo",
            "futuroptimist/futuroptimist",
        ]
    )
    assert exit_code == 0

    first = json.loads(captured_requests[0].data.decode("utf-8"))
    assert first["variables"] == {"owner": "futuroptimist", "name": "futuroptimist"}
    assert "discussionCategories" in first["query"]

    second = json.loads(captured_requests[1].data.decode("utf-8"))
    assert second["variables"]["repositoryId"] == "repo123"
    assert second["variables"]["categoryId"] == "cat456"
    assert second["variables"]["title"].startswith("Fact check: Test Video")
    body = second["variables"]["body"]
    assert slug in body
    assert "https://www.youtube.com/watch?v=abc123" in body

    output = capsys.readouterr().out
    assert "Created discussion" in output


def test_main_uses_default_video_root(tmp_path, monkeypatch, capsys):
    slug = "20240102_default-root"
    video_root = tmp_path / "video_scripts"
    _write_metadata(
        video_root,
        slug,
        {
            "title": "Default Root Video",
        },
    )

    responses = [
        DummyResponse(
            {
                "data": {
                    "repository": {
                        "id": "repo123",
                        "discussionCategories": {
                            "nodes": [
                                {"id": "cat456", "name": "Fact Checks"},
                            ]
                        },
                    }
                }
            }
        ),
        DummyResponse(
            {
                "data": {
                    "createDiscussion": {
                        "discussion": {"url": "https://example.test/discussions/99"}
                    }
                }
            }
        ),
    ]

    monkeypatch.chdir(tmp_path)

    def fake_urlopen(request):
        assert responses, "Unexpected GraphQL call"
        return responses.pop(0)

    monkeypatch.setattr(cfcd.github_auth, "get_github_token", lambda: "token-abc")
    monkeypatch.setattr(cfcd.urllib.request, "urlopen", fake_urlopen)

    exit_code = cfcd.main([slug])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Created discussion" in output


def test_main_errors_when_category_missing(tmp_path, monkeypatch):
    slug = "20240101_missing"
    _write_metadata(tmp_path, slug, {"title": "Missing Category", "youtube_id": "zzz"})

    responses = [
        DummyResponse(
            {
                "data": {
                    "repository": {
                        "id": "repo123",
                        "discussionCategories": {
                            "nodes": [{"id": "cat", "name": "Other"}]
                        },
                    }
                }
            }
        )
    ]

    def fake_urlopen(request):
        assert responses, "Unexpected GraphQL call"
        return responses.pop(0)

    monkeypatch.setattr(cfcd.github_auth, "get_github_token", lambda: "token")
    monkeypatch.setattr(cfcd.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="Fact Checks"):
        cfcd.main(
            [
                slug,
                "--video-root",
                str(tmp_path),
                "--category",
                "Fact Checks",
                "--repo",
                "futuroptimist/futuroptimist",
            ]
        )
