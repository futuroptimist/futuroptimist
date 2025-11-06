"""Utility helpers for the YouTube MCP tool."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from .errors import InvalidArgument

_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def parse_video_id(url_or_id: str) -> str:
    """Extract the YouTube video identifier from a URL or raw ID."""

    candidate = url_or_id.strip()
    if not candidate:
        raise InvalidArgument("Video URL or ID cannot be empty")

    if _VIDEO_ID_RE.fullmatch(candidate):
        return candidate

    parsed = urlparse(candidate)
    if parsed.netloc in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_id = query.get("v", [""])[0]
            if _VIDEO_ID_RE.fullmatch(video_id):
                return video_id
        if parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/")[-1]
            if _VIDEO_ID_RE.fullmatch(video_id):
                return video_id
    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.lstrip("/")
        if _VIDEO_ID_RE.fullmatch(video_id):
            return video_id

    raise InvalidArgument("Could not parse a valid YouTube video ID from the provided value")


def hash_content(obj: Any) -> str:
    """Return a deterministic SHA256 hash for a JSON-serialisable object."""

    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_unlisted_or_private(metadata: dict[str, Any] | None) -> bool:
    """Best-effort detection for unlisted or private videos."""

    if not metadata:
        return False
    visibility = metadata.get("visibility")
    if isinstance(visibility, str) and visibility.lower() in {"private", "unlisted"}:
        return True
    return False
