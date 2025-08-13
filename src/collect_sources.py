import pathlib
import urllib.error
import urllib.parse

from .http_utils import urlopen_http
import json
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
VIDEO_ROOT = BASE_DIR / "video_scripts"
USER_AGENT = "futuroptimist-bot/1.0"


def download_url(url: str, dest: pathlib.Path) -> bool:
    """Download a single URL to ``dest``.

    Returns ``True`` on success and ``False`` if the request fails.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.URLError as exc:
        print(f"Failed to download {url}: {exc}", file=sys.stderr)
        return False


def process_video_dir(video_dir: pathlib.Path) -> None:
    sources_file = video_dir / "sources.txt"
    if not sources_file.exists():
        return

    sources_dir = video_dir / "sources"
    sources_dir.mkdir(exist_ok=True)
    mapping = {}

    lines = [line.strip() for line in sources_file.read_text().splitlines()]
    for idx, url in enumerate(
        [u for u in lines if u and not u.startswith("#")], start=1
    ):
        parsed = urllib.parse.urlparse(url)
        ext = pathlib.Path(parsed.path).suffix
        filename = f"{idx}{ext}"
        dest = sources_dir / filename
        if dest.exists() or download_url(url, dest):
            mapping[url] = dest.name

    (video_dir / "sources.json").write_text(json.dumps(mapping, indent=2) + "\n")


def main() -> None:
    for path in VIDEO_ROOT.iterdir():
        if path.is_dir() and path.name != "__pycache__":
            process_video_dir(path)


if __name__ == "__main__":
    main()
