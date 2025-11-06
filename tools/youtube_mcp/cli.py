"""Command line interface for the YouTube transcript service."""
from __future__ import annotations

import argparse
import json
from typing import Any

from .settings import from_env
from .youtube_client import YouTubeTranscriptService


def _as_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="YouTube transcript helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transcript = subparsers.add_parser("transcript", help="Fetch normalized transcript")
    transcript.add_argument("--url", required=True, help="YouTube URL or ID")
    transcript.add_argument("--lang", help="Preferred language code", default=None)
    transcript.add_argument(
        "--prefer-auto",
        action="store_true",
        help="Prefer auto-generated captions when available.",
    )

    tracks = subparsers.add_parser("tracks", help="List caption tracks")
    tracks.add_argument("--url", required=True, help="YouTube URL or ID")

    metadata = subparsers.add_parser("metadata", help="Fetch basic metadata")
    metadata.add_argument("--url", required=True, help="YouTube URL or ID")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = from_env()
    service = YouTubeTranscriptService(settings=settings)

    if args.command == "transcript":
        transcript = service.get_transcript(args.url, lang=args.lang, prefer_auto=args.prefer_auto)
        print(_as_json(transcript.model_dump()))
        return 0
    if args.command == "tracks":
        tracks = service.list_tracks(args.url)
        print(_as_json({"tracks": [track.model_dump() for track in tracks]}))
        return 0
    if args.command == "metadata":
        metadata = service.get_metadata(args.url)
        print(_as_json(metadata.model_dump()))
        return 0

    parser.error("Unsupported command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
