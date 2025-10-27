"""Upload Futuroptimist videos to YouTube via Data API v3.

This helper fulfils the Phase 8 roadmap promise of providing a draft/private
upload endpoint. It reuses :mod:`src.prepare_youtube_upload` for metadata so the
payload matches existing automation. Credentials are cached locally using the
standard OAuth installed-app flow.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import pathlib
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src import prepare_youtube_upload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_CLIENT_SECRETS = REPO_ROOT / "client_secrets.json"
DEFAULT_CREDENTIALS = (
    pathlib.Path.home() / ".config" / "futuroptimist" / "youtube-upload.json"
)
UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024  # 8 MiB to balance throughput and retries


def load_credentials(
    client_secrets: pathlib.Path, credentials_path: pathlib.Path
) -> Credentials:
    """Return cached OAuth credentials, refreshing or prompting as needed."""

    client_secrets = client_secrets.expanduser().resolve()
    credentials_path = credentials_path.expanduser().resolve()
    credentials_path.parent.mkdir(parents=True, exist_ok=True)

    creds: Credentials | None = None
    if credentials_path.exists():
        creds = Credentials.from_authorized_user_file(str(credentials_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        credentials_path.write_text(creds.to_json())
        return creds
    if not client_secrets.exists():
        raise FileNotFoundError(f"Client secrets not found at {client_secrets}")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    creds = flow.run_console()
    credentials_path.write_text(creds.to_json())
    return creds


def _guess_mimetype(path: pathlib.Path, default: str) -> str:
    mime, _ = mimetypes.guess_type(path.as_posix())
    return mime or default


def upload_video(
    *,
    slug: str,
    repo_root: pathlib.Path,
    video_path: pathlib.Path,
    client_secrets: pathlib.Path,
    credentials_path: pathlib.Path,
    privacy_override: str | None = None,
) -> dict[str, Any]:
    """Upload ``video_path`` for ``slug`` and return the API response."""

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    payload = prepare_youtube_upload.build_upload_package(
        slug,
        repo_root=repo_root,
        privacy_override=privacy_override,
    )
    body = {
        "snippet": payload["snippet"],
        "status": payload["status"],
    }

    credentials = load_credentials(client_secrets, credentials_path)
    service = build("youtube", "v3", credentials=credentials)

    video_media = MediaFileUpload(
        str(video_path),
        mimetype=_guess_mimetype(video_path, "video/mp4"),
        chunksize=UPLOAD_CHUNK_SIZE,
        resumable=True,
    )
    response = (
        service.videos()
        .insert(part="snippet,status", body=body, media_body=video_media)
        .execute()
    )
    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("YouTube API did not return a video ID")

    thumbnail_path = payload.get("thumbnail_path")
    if thumbnail_path:
        thumb_path = pathlib.Path(thumbnail_path)
        if thumb_path.exists():
            thumb_media = MediaFileUpload(
                str(thumb_path),
                mimetype=_guess_mimetype(thumb_path, "image/jpeg"),
                resumable=False,
            )
            service.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
    return {"id": video_id, "response": response}


def _default_video_path(slug: str, repo_root: pathlib.Path) -> pathlib.Path:
    return (repo_root / "dist" / f"{slug}.mp4").resolve()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a Futuroptimist video to YouTube as draft/private",
    )
    parser.add_argument("--slug", required=True, help="Slug like YYYYMMDD_slug")
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=REPO_ROOT,
        help="Repository root containing video_scripts/",
    )
    parser.add_argument(
        "--video",
        type=pathlib.Path,
        default=None,
        help="Path to the rendered video file (defaults to dist/<slug>.mp4)",
    )
    parser.add_argument(
        "--client-secrets",
        type=pathlib.Path,
        default=DEFAULT_CLIENT_SECRETS,
        help="OAuth client secrets JSON path",
    )
    parser.add_argument(
        "--credentials",
        type=pathlib.Path,
        default=DEFAULT_CREDENTIALS,
        help="Credential cache path (stores refresh token)",
    )
    parser.add_argument(
        "--privacy-status",
        dest="privacy_override",
        choices=["public", "private", "unlisted"],
        help="Override privacy status (default inferred from metadata)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prepared payload without uploading",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = args.repo_root.resolve()
    video_path = (
        args.video.resolve()
        if args.video is not None
        else _default_video_path(args.slug, repo_root)
    )
    client_secrets = args.client_secrets
    credentials_path = args.credentials

    if args.dry_run:
        payload = prepare_youtube_upload.build_upload_package(
            args.slug,
            repo_root=repo_root,
            privacy_override=args.privacy_override,
        )
        preview = {k: v for k, v in payload.items() if k in {"snippet", "status"}}
        print(json.dumps(preview, indent=2))
        print(f"Video would upload from {video_path}")
        return 0

    result = upload_video(
        slug=args.slug,
        repo_root=repo_root,
        video_path=video_path,
        client_secrets=client_secrets,
        credentials_path=credentials_path,
        privacy_override=args.privacy_override,
    )
    print(f"Uploaded video {args.slug} to https://youtu.be/{result['id']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
