from types import SimpleNamespace

import pytest

from tools.youtube_mcp import utils


def test_parse_video_id_variants():
    assert utils.parse_video_id("https://www.youtube.com/watch?v=abc123def45") == "abc123def45"
    assert utils.parse_video_id("https://youtu.be/abc123def45?t=10") == "abc123def45"
    assert utils.parse_video_id("https://www.youtube.com/embed/abc123def45") == "abc123def45"
    assert utils.parse_video_id("abc123def45") == "abc123def45"


def test_parse_video_id_invalid_host():
    with pytest.raises(utils.InvalidVideoId):
        utils.parse_video_id("https://example.com/watch?v=abc")


def test_hash_content_is_stable():
    first = utils.hash_content({"a": 1, "b": 2})
    second = utils.hash_content({"b": 2, "a": 1})
    assert first == second


def test_is_unlisted_or_private_detection():
    assert utils.is_unlisted_or_private({"privacy_status": "private"}) is True
    assert utils.is_unlisted_or_private({"is_unlisted": False}) is False


def test_ensure_utf8_handles_non_utf_console(monkeypatch):
    class DummyStdout:
        encoding = "ascii"

        def write(self, value):  # pragma: no cover - not used
            pass

    dummy = DummyStdout()
    monkeypatch.setattr(utils, "sys", SimpleNamespace(stdout=dummy))
    text = "héllo"
    assert isinstance(utils.ensure_utf8(text), str)
