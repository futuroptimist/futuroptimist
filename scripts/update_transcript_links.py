import json
import os
import pathlib
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SCRIPT_ROOT = BASE_DIR / "scripts"
SUBS_DIR = BASE_DIR / "subtitles"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

LIST_URL = "https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={vid}&key={key}"
DOWNLOAD_URL = "https://www.googleapis.com/youtube/v3/captions/{cid}?tfmt=srt&key={key}"


def fetch_transcript(video_id: str) -> pathlib.Path | None:
    if not API_KEY:
        return None
    try:
        with urllib.request.urlopen(LIST_URL.format(vid=video_id, key=API_KEY)) as resp:
            listing = json.loads(resp.read().decode())
        cid = None
        for item in listing.get("items", []):
            lang = item.get("snippet", {}).get("language", "")
            if lang.startswith("en") and not item.get("snippet", {}).get("isDraft"):
                cid = item.get("id")
                break
        if not cid:
            return None
        with urllib.request.urlopen(DOWNLOAD_URL.format(cid=cid, key=API_KEY)) as resp:
            data = resp.read().decode()
        SUBS_DIR.mkdir(exist_ok=True)
        dest = SUBS_DIR / f"{video_id}.srt"
        dest.write_text(data)
        return dest
    except Exception as exc:
        print(f"failed to fetch transcript for {video_id}: {exc}")
        return None


def main() -> None:
    for meta_path in SCRIPT_ROOT.glob("*/metadata.json"):
        data = json.loads(meta_path.read_text())
        vid = data.get("youtube_id")
        if not vid:
            continue
        subtitle_path = SUBS_DIR / f"{vid}.srt"
        if not subtitle_path.exists():
            fetched = fetch_transcript(vid)
            if fetched:
                subtitle_path = fetched
        if subtitle_path.exists():
            relative = subtitle_path.relative_to(BASE_DIR).as_posix()
            if data.get("transcript_file") != relative:
                data["transcript_file"] = relative
                meta_path.write_text(json.dumps(data, indent=2) + "\n")
                print(f"updated {meta_path}")


if __name__ == "__main__":
    main()
