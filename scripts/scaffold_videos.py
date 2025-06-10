import json
import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
IDS_FILE = BASE_DIR / "video_ids.txt"
VIDEO_SCRIPT_ROOT = BASE_DIR / "scripts"
SCHEMA_PATH = BASE_DIR / "schemas" / "video_metadata.schema.json"

TEMPLATE_MD = """# {title}

> Draft script for video `{youtube_id}`

## A-Roll

[NARRATOR]: <!-- narrator lines here -->

## B-Roll / Inserts

[VISUAL]: <!-- description of footage, VFX, AI gen assets, diagrams -->
"""

TEMPLATE_META = {
    "youtube_id": "",
    "title": "",
    "publish_date": "",
    "duration_seconds": 0,
    "keywords": [],
    "status": "draft",
    "description": ""
}


def main():
    if not IDS_FILE.exists():
        sys.exit("video_ids.txt not found")

    # Ensure root scripts directory exists (already does) but create subfolders for videos.
    for vid in [l.strip() for l in IDS_FILE.read_text().splitlines() if l.strip()]:
        vdir = VIDEO_SCRIPT_ROOT / vid
        vdir.mkdir(exist_ok=True)

        # Metadata JSON
        meta_path = vdir / "metadata.json"
        if not meta_path.exists():
            data = TEMPLATE_META.copy()
            data["youtube_id"] = vid
            meta_path.write_text(json.dumps(data, indent=2))
            print(f"Created {meta_path}")

        # Script Markdown
        script_path = vdir / "script.md"
        if not script_path.exists():
            script_path.write_text(TEMPLATE_MD.format(title="TODO", youtube_id=vid))
            print(f"Created {script_path}")


if __name__ == "__main__":
    main() 