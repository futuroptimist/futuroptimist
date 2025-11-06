"""Command line interface for interacting with the transcript service."""

from __future__ import annotations

import argparse
import json

from .youtube_client import YouTubeTranscriptService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="YouTube transcript helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transcript_parser = subparsers.add_parser("transcript", help="Fetch transcript and chunks")
    transcript_parser.add_argument("--url", required=True, help="YouTube video URL or ID")
    transcript_parser.add_argument("--lang", help="Preferred language code", default=None)
    transcript_parser.add_argument(
        "--prefer-auto",
        action="store_true",
        help="Prefer auto-generated captions",
    )

    tracks_parser = subparsers.add_parser("tracks", help="List available caption tracks")
    tracks_parser.add_argument("--url", required=True, help="YouTube video URL or ID")

    metadata_parser = subparsers.add_parser("metadata", help="Fetch metadata only")
    metadata_parser.add_argument("--url", required=True, help="YouTube video URL or ID")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = YouTubeTranscriptService()

    if args.command == "transcript":
        result = service.get_transcript(url=args.url, lang=args.lang, prefer_auto=args.prefer_auto)
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "tracks":
        result = service.list_tracks(url=args.url)
        print(
            json.dumps(
                {"tracks": [track.model_dump() for track in result]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "metadata":
        result = service.get_metadata(url=args.url)
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
