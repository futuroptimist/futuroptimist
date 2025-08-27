import json
import pathlib
import sys
import urllib.request
import re
import datetime

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
IDS_FILE = BASE_DIR / "video_ids.txt"
VIDEO_SCRIPT_ROOT = BASE_DIR / "video_scripts"
SCHEMA_PATH = BASE_DIR / "schemas" / "video_metadata.schema.json"

TEMPLATE_MD = """# {title}

> Draft script for video `{youtube_id}`

## Script

[NARRATOR]: <!-- narrator lines here -->
[VISUAL]: <!-- b-roll, graphics, or stage directions -->
"""

TEMPLATE_META = {
    "youtube_id": "",
    "title": "",
    "publish_date": "",
    "duration_seconds": 0,
    "keywords": [],
    "status": "draft",
    "description": "",
    "slug": "",
    "thumbnail": "",
    "transcript_file": "",
    "summary": "",
}


def read_video_ids():
    ids = []
    for line in IDS_FILE.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            ids.append(stripped)
    return ids


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def fetch_video_info(video_id: str):
    url = f"https://r.jina.ai/https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req).read().decode("utf-8", "ignore")
    title_match = re.search(r"^Title: (.+)", html, re.MULTILINE)
    date_match = re.search(r"([A-Z][a-z]+ [0-9]{1,2}, [0-9]{4})", html)
    if not (title_match and date_match):
        raise RuntimeError(f"Unable to parse metadata for {video_id}")
    title = title_match.group(1).strip()
    date = datetime.datetime.strptime(date_match.group(1), "%b %d, %Y")
    return title, date.strftime("%Y%m%d")


def main():
    if not IDS_FILE.exists():
        sys.exit("video_ids.txt not found")

    for vid in read_video_ids():
        try:
            title, date_str = fetch_video_info(vid)
        except Exception as e:  # network or parse failure
            print(f"Failed to fetch info for {vid}: {e}")
            continue
        slug = slugify(title)
        folder_name = f"{date_str}_{slug}"
        vdir = VIDEO_SCRIPT_ROOT / folder_name
        vdir.mkdir(exist_ok=True)

        meta_path = vdir / "metadata.json"
        if not meta_path.exists():
            data = TEMPLATE_META.copy()
            data["youtube_id"] = vid
            data["title"] = title
            data["publish_date"] = datetime.datetime.strptime(
                date_str, "%Y%m%d"
            ).strftime("%Y-%m-%d")
            data["slug"] = slug
            data["transcript_file"] = f"subtitles/{vid}.srt"
            meta_path.write_text(json.dumps(data, indent=2) + "\n")
            print(f"Created {meta_path}")

        script_path = vdir / "script.md"
        if not script_path.exists():
            script_path.write_text(TEMPLATE_MD.format(title=title, youtube_id=vid))
            print(f"Created {script_path}")

        footage_path = vdir / "footage.md"
        if not footage_path.exists():
            footage_path.write_text("# Footage Checklist\n\n- [ ] \n")
            print(f"Created {footage_path}")


if __name__ == "__main__":
    main()
