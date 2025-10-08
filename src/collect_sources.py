import os
import pathlib
import urllib.request
import urllib.error
import urllib.parse
import json
import sys
from typing import Iterable

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
VIDEO_ROOT = BASE_DIR / "video_scripts"
SOURCE_URLS_FILE = BASE_DIR / "source_urls.txt"
GLOBAL_SOURCES_DIR = BASE_DIR / "sources"
SOURCE_URLS_ENV = "FUTUROPTIMIST_SOURCE_URLS_FILE"
GLOBAL_SOURCES_ENV = "FUTUROPTIMIST_SOURCES_DIR"
USER_AGENT = "futuroptimist-bot/1.0"
URL_TIMEOUT = 10


def download_url(url: str, dest: pathlib.Path) -> bool:
    """Download a single URL to ``dest``.

    Uses a ``10s`` timeout and returns ``True`` on success, ``False`` on any
    network ``URLError`` or local ``OSError`` such as a write failure.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=URL_TIMEOUT) as resp:
            dest.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, OSError) as exc:
        print(f"Failed to download {url}: {exc}", file=sys.stderr)
        return False


def process_video_dir(video_dir: pathlib.Path) -> None:
    sources_file = video_dir / "sources.txt"
    if not sources_file.exists():
        return

    sources_dir = video_dir / "sources"
    sources_dir.mkdir(exist_ok=True)
    urls = _filter_urls(sources_file.read_text().splitlines())
    mapping = _download_sources(urls, sources_dir)

    (video_dir / "sources.json").write_text(json.dumps(mapping, indent=2) + "\n")


def _filter_urls(lines: Iterable[str]) -> list[str]:
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def _download_sources(urls: Iterable[str], dest_dir: pathlib.Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    dest_dir.mkdir(exist_ok=True)
    for idx, url in enumerate(urls, start=1):
        parsed = urllib.parse.urlparse(url)
        ext = pathlib.Path(parsed.path).suffix
        filename = f"{idx}{ext}"
        dest = dest_dir / filename
        if dest.exists() or download_url(url, dest):
            mapping[url] = dest.name
    return mapping


def _resolve_source_urls_file(source_file: pathlib.Path | None = None) -> pathlib.Path:
    if source_file is not None:
        return source_file
    override = os.environ.get(SOURCE_URLS_ENV, "").strip()
    if override:
        expanded = os.path.expandvars(override)
        expanded = os.path.expanduser(expanded)
        return pathlib.Path(expanded)
    return SOURCE_URLS_FILE


def _resolve_global_sources_dir(dest_dir: pathlib.Path | None = None) -> pathlib.Path:
    if dest_dir is not None:
        return dest_dir
    override = os.environ.get(GLOBAL_SOURCES_ENV, "").strip()
    if override:
        expanded = os.path.expandvars(override)
        expanded = os.path.expanduser(expanded)
        return pathlib.Path(expanded)
    return GLOBAL_SOURCES_DIR


def process_global_sources(
    source_file: pathlib.Path | None = None,
    dest_dir: pathlib.Path | None = None,
) -> dict[str, str]:
    source_path = _resolve_source_urls_file(source_file)
    if not source_path.exists():
        return {}
    urls = _filter_urls(source_path.read_text().splitlines())
    target_dir = _resolve_global_sources_dir(dest_dir)
    mapping = _download_sources(urls, target_dir)
    output = target_dir / "sources.json"
    output.write_text(json.dumps(mapping, indent=2) + "\n")
    return mapping


def main() -> None:
    process_global_sources()
    for path in VIDEO_ROOT.iterdir():
        if path.is_dir() and path.name != "__pycache__":
            process_video_dir(path)


if __name__ == "__main__":
    main()
