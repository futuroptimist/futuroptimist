"""Utility helpers for the YouTube MCP service."""
from __future__ import annotations

import json
import re
import time
from hashlib import sha256
from typing import Any
from urllib.parse import parse_qs, urlparse

from .errors import InvalidArgument

_YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def parse_video_id(url_or_id: str) -> str:
    """Extract the canonical video identifier from a URL or raw ID."""

    value = url_or_id.strip()
    if not value:
        raise InvalidArgument("Video URL or ID must not be empty.")

    if _YOUTUBE_ID_PATTERN.fullmatch(value):
        return value

    parsed = urlparse(value)
    if parsed.netloc in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if _YOUTUBE_ID_PATTERN.fullmatch(video_id):
            return video_id
    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        path = parsed.path.strip("/")
        if _YOUTUBE_ID_PATTERN.fullmatch(path):
            return path

    raise InvalidArgument("Unsupported or invalid YouTube URL/ID.")


def hash_content(obj: Any) -> str:
    """Generate a deterministic SHA-256 hash for JSON-serializable content."""

    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload).hexdigest()


def build_watch_url(video_id: str) -> str:
    """Return the canonical watch URL for a video."""

    return f"https://www.youtube.com/watch?v={video_id}"


def build_cite_url(video_id: str, start_seconds: float) -> str:
    """Generate a citeable URL anchored to the given timestamp."""

    ts = int(max(start_seconds, 0))
    return f"{build_watch_url(video_id)}&t={ts}s"


def epoch_seconds() -> int:
    """Return the current UNIX timestamp in seconds."""

    return int(time.time())


def is_unlisted_or_private(_: Any) -> bool:
    """Best-effort detection for restricted videos.

    Without authenticated APIs this currently returns ``False`` to avoid
    accidental false positives. The helper exists so future improvements can
    slot in more robust checks without touching the call sites.
    """

    return False
