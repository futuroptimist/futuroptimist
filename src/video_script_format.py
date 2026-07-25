"""Parse, validate, and canonically format Futuroptimist video scripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "video_script.schema.json"
SOURCE_RE = re.compile(r"^> (Draft script|Transcript) for video `([^`]+)`$")
LEGACY_SOURCE_RE = re.compile(r"^> YouTube ID:\s*(\S+)\s*$")
TAG_RE = re.compile(r"^\[(NARRATOR|VISUAL)\]:(?: (.*))?$")
TIMING_RE = re.compile(r"\s*<!--\s*(.*?)\s*(?:->|→)\s*(.*?)\s*-->\s*$")
TIMED_SECTION_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?\s*(?:-|–|—|→)\s*"
    r"\d{1,2}:\d{2}(?::\d{2})?\s*:\s*\S.*$"
)
SENTINEL_VIDEO_IDS = {"draft", "<youtube_id>"}


class ScriptFormatError(ValueError):
    """A line-oriented script format error."""

    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.line = line


def parse_script(text: str, *, migrate: bool = False) -> dict:
    """Parse Markdown into the normalized schema object."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        raise ScriptFormatError("expected one nonempty H1 title at the start", 1)
    title = lines[0][2:].strip()
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        raise ScriptFormatError("missing canonical source blockquote", i + 1)
    match = SOURCE_RE.fullmatch(lines[i])
    if not match and migrate:
        legacy = LEGACY_SOURCE_RE.fullmatch(lines[i])
        if legacy:
            match_values = ("Draft script", legacy.group(1))
        else:
            match_values = None
    else:
        match_values = match.groups() if match else None
    if not match_values:
        raise ScriptFormatError(
            "expected canonical source '> Draft script for video `id`' or transcript header",
            i + 1,
        )
    source, video_id = match_values
    kind = "draft" if source == "Draft script" else "transcript"
    i += 1
    outline: list[str] = []
    while i < len(lines) and not lines[i].strip():
        i += 1
    if migrate and i < len(lines) and lines[i].strip() == "> Draft outline":
        i += 1
        while i < len(lines) and lines[i].strip() != "## Script":
            value = lines[i].strip()
            if value.startswith(">"):
                value = value[1:].strip()
                if value:
                    outline.append(value)
            elif value:
                raise ScriptFormatError("invalid legacy outline line", i + 1)
            i += 1
    elif i < len(lines) and lines[i].strip() == "## Outline":
        i += 1
        while i < len(lines) and lines[i].strip() != "## Script":
            value = lines[i].strip()
            if value:
                if not value.startswith("- ") or not value[2:].strip():
                    raise ScriptFormatError(
                        "outline entries must be nonempty '- ' items", i + 1
                    )
                outline.append(value[2:])
            i += 1
    if i >= len(lines) or lines[i].strip() != "## Script":
        raise ScriptFormatError("missing ## Script heading", i + 1)
    i += 1
    segments: list[dict] = []
    while i < len(lines):
        raw = lines[i]
        value = raw.strip()
        if not value:
            i += 1
            continue
        if value.startswith("### ") and value[4:].strip():
            segments.append({"type": "section", "text": value[4:].strip()})
        elif migrate and value.startswith(">") and value[1:].strip():
            section_text = value[1:].strip()
            if not TIMED_SECTION_RE.fullmatch(section_text):
                raise ScriptFormatError(
                    "cannot migrate body blockquote; expected a timed section label "
                    "such as '> 0:01-0:02: Section title'",
                    i + 1,
                )
            segments.append({"type": "section", "text": section_text})
        else:
            tag = TAG_RE.fullmatch(raw)
            if not tag:
                raise ScriptFormatError(
                    "script body must be ###, [NARRATOR]:, or [VISUAL]:", i + 1
                )
            segment_type = tag.group(1).lower()
            segment_text = tag.group(2) or ""
            if not segment_text.strip():
                raise ScriptFormatError(f"empty {segment_type} segment", i + 1)
            segment = {"type": segment_type, "text": segment_text}
            if segment_type == "narrator":
                timing = TIMING_RE.search(segment_text)
                if timing:
                    segment["timing"] = {
                        "start": timing.group(1),
                        "end": timing.group(2),
                    }
            segments.append(segment)
        i += 1
    document = {"schema_version": 1, "title": title, "kind": kind, "video_id": video_id}
    if outline:
        document["outline"] = outline
    document["segments"] = segments
    return document


def validate_document(document: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft7Validator(schema).iter_errors(document),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ScriptFormatError("schema: " + errors[0].message)


def format_document(document: dict) -> str:
    """Render a normalized document with exactly one blank line between blocks."""
    source = "Draft script" if document["kind"] == "draft" else "Transcript"
    blocks = [
        f"# {document['title']}",
        f"> {source} for video `{document['video_id']}`",
    ]
    if document.get("outline"):
        blocks.extend(
            ["## Outline", "\n".join(f"- {item}" for item in document["outline"])]
        )
    blocks.append("## Script")
    for segment in document["segments"]:
        if segment["type"] == "section":
            blocks.append(f"### {segment['text']}")
        else:
            blocks.append(f"[{segment['type'].upper()}]: {segment['text']}")
    return "\n\n".join(blocks) + "\n"


def validate_metadata(path: Path, document: dict) -> None:
    metadata_path = path.with_name("metadata.json")
    if not metadata_path.exists():
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ScriptFormatError("metadata.json must contain a JSON object")
    metadata_youtube_id = metadata.get("youtube_id", "")
    youtube_id = "" if metadata_youtube_id is None else str(metadata_youtube_id).strip()
    if (
        youtube_id
        and youtube_id not in SENTINEL_VIDEO_IDS
        and document["video_id"] != youtube_id
    ):
        raise ScriptFormatError(
            f"video id {document['video_id']!r} does not match metadata {youtube_id!r}",
            3,
        )


def process(path: Path, *, write: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    document = parse_script(original, migrate=write)
    validate_document(document)
    validate_metadata(path, document)
    canonical = format_document(document)
    if write:
        if original != canonical:
            path.write_text(canonical, encoding="utf-8")
            return True
    elif original != canonical:
        raise ScriptFormatError("not canonically formatted; run with --write", 1)
    return False


def discover(paths: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for path in paths:
        if path.is_dir():
            found.update(path.rglob("script.md"))
        elif path.name == "script.md":
            found.add(path)
    return sorted(found)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = False
    scripts: set[Path] = set()
    for path in args.paths:
        if not path.exists():
            print(f"{path}:1: input does not exist", file=sys.stderr)
            failed = True
        elif path.is_dir():
            discovered = set(path.rglob("script.md"))
            if not discovered:
                print(
                    f"{path}:1: directory contains no script.md files", file=sys.stderr
                )
                failed = True
            scripts.update(discovered)
        elif path.name == "script.md":
            scripts.add(path)
        else:
            print(f"{path}:1: input is not a script.md file", file=sys.stderr)
            failed = True
    for path in sorted(scripts):
        try:
            changed = process(path, write=args.write)
            if changed:
                print(f"Formatted {path}")
        except (OSError, ScriptFormatError, json.JSONDecodeError) as error:
            line = getattr(error, "line", 1)
            print(f"{path}:{line}: {error}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
