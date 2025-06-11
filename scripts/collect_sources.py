import pathlib
import urllib.request
import urllib.error
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
URLS_FILE = BASE_DIR / "source_urls.txt"
OUTPUT_DIR = BASE_DIR / "sources"


def read_urls():
    if not URLS_FILE.exists():
        sys.stderr.write(f"URLs file {URLS_FILE} not found.\n")
        return []
    return [u.strip() for u in URLS_FILE.read_text().splitlines() if u.strip()]


def download_url(url: str, dest: pathlib.Path) -> bool:
    try:
        with urllib.request.urlopen(url) as resp, open(dest, "wb") as fh:
            fh.write(resp.read())
        return True
    except urllib.error.URLError as e:
        print(f"Failed to download {url}: {e}")
        return False


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    for url in read_urls():
        filename = url.split("/")[-1] or "index.html"
        dest = OUTPUT_DIR / filename
        if download_url(url, dest):
            print(f"Saved {dest}")


if __name__ == "__main__":
    main()
