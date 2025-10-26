"""Build a YouTube upload payload from Futuroptimist metadata.

Phase 8 of ``INSTRUCTIONS.md`` promises automatic attachment of
thumbnails and metadata when preparing uploads. This helper reads a
video slug's ``metadata.json``, resolves the thumbnail path from the
repository, maps Futuroptimist status values onto YouTube privacy
statuses, and writes a JSON payload ready for an uploader to consume.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VIDEO_ROOT = pathlib.Path("video_scripts")
DEFAULT_PRIVACY = "private"
_STATUS_TO_PRIVACY: dict[str, str] = {
    "draft": "private",
    "private": "private",
    "ready": "unlisted",
    "scheduled": "private",
    "live": "public",
    "public": "public",
    "unlisted": "unlisted",
}


def _load_metadata(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Failed to parse {path}: {exc}") from exc


def _normalise_tags(raw: str | Iterable[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [token.strip() for token in raw.split(",") if token.strip()]
    tags: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            tags.append(text)
    return tags


def _privacy_from_status(status: str | None, override: str | None) -> str:
    if override:
        token = override.strip().lower()
        if token in {"public", "private", "unlisted"}:
            return token
        raise ValueError(
            "privacy_override must be one of 'public', 'private', or 'unlisted'"
        )
    if not status:
        return DEFAULT_PRIVACY
    token = status.strip().lower()
    return _STATUS_TO_PRIVACY.get(token, DEFAULT_PRIVACY)


def _resolve_thumbnail(
    slug_dir: pathlib.Path, repo_root: pathlib.Path, thumbnail: str | None
) -> tuple[str | None, str | None]:
    if not thumbnail:
        return None, None
    token = thumbnail.strip()
    if not token:
        return None, None
    if token.startswith(("http://", "https://")):
        return None, token

    candidate = pathlib.Path(token)
    search_paths = []
    if candidate.is_absolute():
        search_paths.append(candidate)
    else:
        search_paths.append(repo_root / candidate)
        search_paths.append(slug_dir / candidate)
    for path in search_paths:
        if path.exists():
            return str(path.resolve()), None
    raise FileNotFoundError(
        f"Thumbnail '{thumbnail}' not found for slug {slug_dir.name}"
    )


def build_upload_package(
    slug: str,
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    privacy_override: str | None = None,
    output_path: pathlib.Path | None = None,
) -> dict:
    """Return an upload payload for ``slug`` and optionally write it to disk."""

    slug = slug.strip()
    if not slug:
        raise ValueError("slug cannot be blank")

    repo_root = repo_root.resolve()
    video_dir = (repo_root / VIDEO_ROOT / slug).resolve()
    metadata_path = video_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found for slug {slug}")

    metadata = _load_metadata(metadata_path)
    title = str(metadata.get("title", "")).strip()
    if not title:
        raise ValueError(f"metadata for {slug} is missing a title")
    description = str(metadata.get("description", "") or "")
    tags = _normalise_tags(metadata.get("keywords"))

    thumbnail_path, thumbnail_url = _resolve_thumbnail(
        video_dir, repo_root, metadata.get("thumbnail")
    )

    snippet = {
        "title": title,
        "description": description,
        "tags": tags,
    }
    privacy = _privacy_from_status(metadata.get("status"), privacy_override)
    payload = {
        "slug": slug,
        "metadata_path": str(metadata_path.resolve()),
        "snippet": snippet,
        "status": {"privacyStatus": privacy},
    }
    if metadata.get("publish_date") and privacy != "public":
        payload["status"]["publishAt"] = metadata["publish_date"]
    if thumbnail_path:
        payload["thumbnail_path"] = thumbnail_path
    if thumbnail_url:
        payload["thumbnail_url"] = thumbnail_url

    if output_path is not None:
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build YouTube upload payload from Futuroptimist metadata",
    )
    parser.add_argument("--slug", required=True, help="Slug folder like YYYYMMDD_slug")
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=REPO_ROOT,
        help="Repository root containing video_scripts/",
    )
    parser.add_argument(
        "--privacy-status",
        dest="privacy_override",
        choices=["public", "private", "unlisted"],
        help="Override privacy status (default inferred from metadata.status)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Optional JSON output path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = build_upload_package(
        args.slug,
        repo_root=args.repo_root,
        privacy_override=args.privacy_override,
        output_path=args.output,
    )
    print(
        f"Prepared upload payload for {args.slug} (privacy={payload['status']['privacyStatus']})"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
