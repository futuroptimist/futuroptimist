"""Command line interface for the YouTube MCP service."""

from __future__ import annotations

import argparse
import json
import sys

from pydantic import BaseModel

from .errors import BaseYtMcpError
from .settings import Settings
from .utils import ensure_utf8
from .youtube_client import YouTubeTranscriptService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="YouTube transcript helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transcript_parser = subparsers.add_parser(
        "transcript", help="Fetch transcript JSON"
    )
    transcript_parser.add_argument(
        "--url", required=True, help="YouTube video URL or ID"
    )
    transcript_parser.add_argument("--lang", help="Preferred language code")
    transcript_parser.add_argument(
        "--prefer-auto",
        action="store_true",
        help="Prefer auto-generated captions when available",
    )

    tracks_parser = subparsers.add_parser(
        "tracks", help="List available caption tracks"
    )
    tracks_parser.add_argument("--url", required=True, help="YouTube video URL or ID")

    metadata_parser = subparsers.add_parser("metadata", help="Fetch video metadata")
    metadata_parser.add_argument("--url", required=True, help="YouTube video URL or ID")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    service = YouTubeTranscriptService(settings=settings)

    result: BaseModel
    try:
        if args.command == "transcript":
            result = service.get_transcript(
                args.url, lang=args.lang, prefer_auto=args.prefer_auto
            )
        elif args.command == "tracks":
            result = service.search_captions(args.url)
        elif args.command == "metadata":
            result = service.get_metadata(args.url)
        else:  # pragma: no cover - argparse ensures known commands
            parser.error(f"Unknown command: {args.command}")
            return 2
    except BaseYtMcpError as exc:
        print(ensure_utf8(json.dumps(exc.to_dict(), indent=2)), file=sys.stderr)
        return 1

    print(ensure_utf8(result.model_dump_json(indent=2)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
