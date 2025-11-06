"""Utility helpers for the YouTube MCP package."""

from __future__ import annotations

import json
import re
import sys
from hashlib import sha256
from typing import Any
from urllib.parse import parse_qs, urlparse

_YOUTUBE_WATCH_BASE = "https://www.youtube.com/watch"
_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


class InvalidVideoIdError(ValueError):
    """Raised when a YouTube URL or identifier cannot be parsed."""


# Backwards compatibility alias for legacy imports within the package.
InvalidVideoId = InvalidVideoIdError


def parse_video_id(url_or_id: str) -> str:
    """Extract a canonical video identifier from a URL or ID string."""

    candidate = (url_or_id or "").strip()
    if not candidate:
        raise InvalidVideoId("Video identifier cannot be empty")

    parsed = urlparse(candidate)
    if parsed.scheme and parsed.netloc:
        host = parsed.netloc.lower()
        if host not in _YOUTUBE_HOSTS:
            raise InvalidVideoId(f"Unsupported YouTube host: {host}")

        if host in {"youtu.be", "www.youtu.be"}:
            video_id = parsed.path.lstrip("/")
            video_id = video_id.split("/")[0]
            video_id = video_id.split("?")[0]
        else:
            if parsed.path.startswith("/embed/"):
                video_id = parsed.path.split("/embed/")[-1].split("/")[0]
            elif parsed.path.startswith("/shorts/"):
                video_id = parsed.path.split("/shorts/")[-1].split("/")[0]
            else:
                query = parse_qs(parsed.query)
                video_candidates = query.get("v")
                if not video_candidates:
                    raise InvalidVideoId("Missing 'v' parameter in YouTube URL")
                video_id = video_candidates[0]
    else:
        video_id = candidate

    if not re.fullmatch(r"[0-9A-Za-z_-]{11}", video_id):
        raise InvalidVideoId(f"Invalid YouTube video identifier: {video_id}")

    return video_id


def build_watch_url(video_id: str) -> str:
    """Construct a canonical YouTube watch URL for the given video ID."""

    return f"{_YOUTUBE_WATCH_BASE}?v={video_id}"


def hash_content(obj: Any) -> str:
    """Compute a deterministic sha256 hash for JSON-serialisable data."""

    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def is_unlisted_or_private(metadata: Any) -> bool:
    """Best-effort detection of private or unlisted videos.

    The oEmbed endpoint does not expose privacy flags, so this function conservatively
    returns :data:`False` unless explicit markers are present.
    """

    if metadata is None:
        return False

    if isinstance(metadata, dict):
        lowered = {str(key).lower(): value for key, value in metadata.items()}
        for key in ("is_unlisted", "is_private", "privacy_status"):
            value = lowered.get(key)
            if isinstance(value, str) and value.lower() in {"true", "private", "unlisted"}:
                return True
            if isinstance(value, bool) and value:
                return True
    return False


def ensure_utf8(text: str) -> str:
    """Ensure text is encoded as UTF-8 when writing to stdio."""

    if sys.stdout.encoding and sys.stdout.encoding.lower() == "utf-8":
        return text
    return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
