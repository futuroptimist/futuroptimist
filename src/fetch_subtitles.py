import subprocess
import pathlib
import sys
import shutil

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
IDS_FILE = BASE_DIR / "video_ids.txt"
OUTPUT_DIR = BASE_DIR / "subtitles"


def ensure_requirements():
    """Check that yt-dlp is installed."""
    if shutil.which("yt-dlp") is None:
        sys.stderr.write(
            "yt-dlp executable not found in PATH. Install via uv: uv pip install yt-dlp\n"
        )
        sys.exit(1)


def read_video_ids():
    if not IDS_FILE.exists():
        sys.stderr.write(f"IDs file {IDS_FILE} not found.\n")
        sys.exit(1)
    return [line.strip() for line in IDS_FILE.read_text().splitlines() if line.strip()]


def download_subtitles(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    # --skip-download avoids video download; --write-sub fetches manual captions only.
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-sub",
        "--sub-lang",
        "en.*",
        "--convert-subs",
        "srt",
        "-o",
        str(OUTPUT_DIR / "%(id)s.%(ext)s"),
        url,
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(
            "Primary download failed – retrying without SRT conversion (raw .vtt will be kept)"
        )
        cmd_fallback = [
            "yt-dlp",
            "--skip-download",
            "--write-sub",
            "--sub-lang",
            "en.*",
            "-o",
            str(OUTPUT_DIR / "%(id)s.%(ext)s"),
            url,
        ]
        subprocess.run(cmd_fallback, check=True)


def main():
    ensure_requirements()
    OUTPUT_DIR.mkdir(exist_ok=True)
    ids = read_video_ids()
    for vid in ids:
        try:
            print(f"Downloading subtitles for {vid}...")
            download_subtitles(vid)
        except subprocess.CalledProcessError as e:
            print(f"Failed for {vid}: {e}")


if __name__ == "__main__":
    main()
