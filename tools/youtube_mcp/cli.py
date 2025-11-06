"""Command line interface for the YouTube transcript service."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .cache import Cache
from .errors import BaseYtMcpError
from .settings import Settings
from .youtube_client import YouTubeTranscriptService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="YouTube MCP utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transcript_parser = subparsers.add_parser("transcript", help="Fetch transcript")
    transcript_parser.add_argument("--url", required=True, help="Video URL or ID")
    transcript_parser.add_argument("--lang", help="Preferred language code")
    transcript_parser.add_argument(
        "--prefer-auto",
        action="store_true",
        help="Prefer auto-generated captions when available",
    )

    tracks_parser = subparsers.add_parser("tracks", help="List caption tracks")
    tracks_parser.add_argument("--url", required=True, help="Video URL or ID")

    metadata_parser = subparsers.add_parser("metadata", help="Fetch metadata only")
    metadata_parser.add_argument("--url", required=True, help="Video URL or ID")

    return parser


def _service_from_settings(settings: Settings) -> YouTubeTranscriptService:
    cache = Cache(settings.cache_dir / "transcripts.sqlite3", settings.cache_ttl_days)
    return YouTubeTranscriptService(settings, cache)


def _print(obj: Any) -> None:
    json.dump(obj, fp=sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    service = _service_from_settings(settings)

    try:
        if args.command == "transcript":
            response = service.get_transcript(
                args.url,
                lang=args.lang,
                prefer_auto=args.prefer_auto,
            )
            _print(response.model_dump())
        elif args.command == "tracks":
            tracks = service.list_tracks(args.url)
            _print({"tracks": [track.model_dump() for track in tracks]})
        elif args.command == "metadata":
            metadata = service.get_metadata(args.url)
            _print(metadata.model_dump())
        else:  # pragma: no cover - argparse guards this
            parser.error(f"Unknown command {args.command}")
    except BaseYtMcpError as exc:
        _print({"error": exc.to_dict()})
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
