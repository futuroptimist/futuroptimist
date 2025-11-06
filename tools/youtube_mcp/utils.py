"""Helper utilities for parsing IDs, hashing, and citation URLs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from .errors import InvalidArgument

YOUTUBE_ID_PATTERN = re.compile(r"^[0-9A-Za-z_-]{6,}=?$")


def parse_video_id(url_or_id: str) -> str:
    """Extract a YouTube video ID from a URL or raw identifier."""

    candidate = url_or_id.strip()
    if not candidate:
        raise InvalidArgument("InvalidArgument", "Empty URL or video identifier provided")

    parsed = urlparse(candidate)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc.endswith("youtu.be"):
            video_id = parsed.path.lstrip("/")
        else:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [""])[0]
        if not video_id:
            raise InvalidArgument("InvalidArgument", "Could not parse video ID from URL")
    else:
        video_id = candidate

    video_id = video_id.strip()
    if not YOUTUBE_ID_PATTERN.match(video_id):
        raise InvalidArgument("InvalidArgument", "Video ID contains unexpected characters")

    return video_id


def build_watch_url(video_id: str) -> str:
    """Return the canonical watch URL for the given video ID."""

    return f"https://www.youtube.com/watch?v={video_id}"


def build_cite_url(video_id: str, start_seconds: float) -> str:
    """Return a timecoded citation URL for the provided start time."""

    seconds = max(0, int(start_seconds))
    return f"{build_watch_url(video_id)}&t={seconds}s"


def hash_content(obj: Any) -> str:
    """Compute a deterministic SHA256 hash for an arbitrary JSON-serialisable object."""

    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = ["build_cite_url", "build_watch_url", "hash_content", "parse_video_id"]
