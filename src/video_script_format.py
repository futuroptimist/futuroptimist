"""Parse, validate, and canonically format Futuroptimist ``script.md`` files."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass

import jsonschema

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "video_script.schema.json"
SOURCE_RE = re.compile(r"^> (Draft script|Transcript) for video `([^`]+)`$")
LEGACY_SOURCE_RE = re.compile(r"^> YouTube ID:\s*(\S+)\s*$", re.I)
TAG_RE = re.compile(r"^\[(NARRATOR|VISUAL)\]:\s*(.*)$")
TIMING_RE = re.compile(r"\s*<!--\s*([0-9:,]+)\s*->\s*([0-9:,]+)\s*-->\s*$")


class ScriptFormatError(ValueError):
    """A script cannot be parsed without guessing at its content."""

    def __init__(self, line: int, message: str):
        super().__init__(message)
        self.line = line


@dataclass(slots=True)
class ParsedScript:
    data: dict

    @property
    def segments(self) -> list[dict]:
        return self.data["segments"]


def _fail(line: int, message: str) -> None:
    raise ScriptFormatError(line, message)


def parse_script(text: str, *, legacy: bool = False) -> ParsedScript:
    """Parse canonical Markdown, optionally recognizing known legacy structures."""

    lines = text.splitlines()
    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        _fail(1, "expected a nonempty H1 title at the start")
    title = lines[0][2:].strip()
    source_index = next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip()), None
    )
    if source_index is None:
        _fail(2, "missing canonical source blockquote")
    source = SOURCE_RE.fullmatch(lines[source_index].strip())
    if source:
        kind = "draft" if source.group(1).startswith("Draft") else "transcript"
        video_id = source.group(2).strip()
    elif legacy and (match := LEGACY_SOURCE_RE.fullmatch(lines[source_index].strip())):
        kind, video_id = "draft", match.group(1)
    else:
        _fail(
            source_index + 1,
            "expected canonical Draft script or Transcript source header",
        )
    if not video_id:
        _fail(source_index + 1, "video identifier cannot be empty")

    script_index = next(
        (
            i
            for i in range(source_index + 1, len(lines))
            if lines[i].strip() == "## Script"
        ),
        None,
    )
    if script_index is None:
        _fail(source_index + 2, "missing ## Script heading")

    outline: list[str] = []
    before_script = lines[source_index + 1 : script_index]
    if legacy and any(line.strip() == "> Draft outline" for line in before_script):
        for line in before_script:
            value = line.strip()
            if value.startswith("> ") and value != "> Draft outline":
                outline.append(value[2:].strip())
    else:
        meaningful = [
            (source_index + 2 + i, line.strip())
            for i, line in enumerate(before_script)
            if line.strip()
        ]
        if meaningful:
            if meaningful[0][1] != "## Outline":
                _fail(
                    meaningful[0][0], "only optional ## Outline may precede ## Script"
                )
            for number, line in meaningful[1:]:
                if not line.startswith("- ") or not line[2:].strip():
                    _fail(number, "outline entries must be nonempty '- ' list items")
                outline.append(line[2:].strip())

    segments: list[dict] = []
    for index, raw in enumerate(lines[script_index + 1 :], script_index + 2):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("### ") and line[4:].strip():
            segments.append({"type": "section", "text": line[4:].strip()})
            continue
        if legacy and line.startswith("> ") and line != ">":
            segments.append({"type": "section", "text": line[2:].strip()})
            continue
        match = TAG_RE.fullmatch(line)
        if not match:
            if line.startswith("["):
                _fail(index, "unknown or malformed script-body tag")
            _fail(index, "untagged script-body prose is not allowed")
        segment_type = match.group(1).lower()
        segment_text = match.group(2).strip()
        if not segment_text:
            _fail(index, f"empty {segment_type} segment")
        segment: dict = {"type": segment_type, "text": segment_text}
        if segment_type == "narrator" and (timing := TIMING_RE.search(segment_text)):
            segment["text"] = segment_text[: timing.start()].rstrip()
            segment["timing"] = {"start": timing.group(1), "end": timing.group(2)}
            if not segment["text"]:
                _fail(index, "empty narrator segment before timing comment")
        segments.append(segment)
    if not segments:
        _fail(script_index + 1, "script must contain at least one segment")
    data = {
        "schema_version": 1,
        "title": title,
        "document_kind": kind,
        "video_id": video_id,
        "segments": segments,
    }
    if outline:
        data["outline"] = outline
    return ParsedScript(data)


def format_script(parsed: ParsedScript) -> str:
    """Render the normalized representation with deterministic spacing."""

    data = parsed.data
    label = "Draft script" if data["document_kind"] == "draft" else "Transcript"
    blocks = [f"# {data['title']}", f"> {label} for video `{data['video_id']}`"]
    outline = data.get("outline", [])
    if outline:
        blocks.extend(["## Outline", "\n".join(f"- {item}" for item in outline)])
    blocks.append("## Script")
    for segment in data["segments"]:
        if segment["type"] == "section":
            blocks.append(f"### {segment['text']}")
        else:
            tag = segment["type"].upper()
            value = f"[{tag}]: {segment['text']}"
            if segment.get("timing"):
                timing = segment["timing"]
                value += f"  <!-- {timing['start']} -> {timing['end']} -->"
            blocks.append(value)
    return "\n\n".join(blocks) + "\n"


def validate_script(parsed: ParsedScript, path: pathlib.Path | None = None) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(parsed.data, schema)
    if path is None:
        return
    metadata_path = path.parent / "metadata.json"
    if not metadata_path.exists():
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata_id = str(metadata.get("youtube_id", "")).strip()
    script_id = parsed.data["video_id"]
    sentinels = {"draft", "<youtube_id>"}
    if (
        metadata_id
        and metadata_id not in sentinels
        and script_id not in sentinels
        and metadata_id != script_id
    ):
        raise ScriptFormatError(
            3, f"video ID {script_id!r} does not match metadata {metadata_id!r}"
        )


def discover_scripts(path: pathlib.Path) -> list[pathlib.Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("script.md"))


def process(path: pathlib.Path, *, write: bool) -> list[str]:
    errors: list[str] = []
    for script_path in discover_scripts(path):
        original = script_path.read_text(encoding="utf-8")
        try:
            parsed = parse_script(original, legacy=write)
            validate_script(parsed, script_path)
            canonical = format_script(parsed)
            if write:
                if canonical != original:
                    script_path.write_text(canonical, encoding="utf-8")
                    print(f"Formatted {script_path}")
            elif canonical != original:
                errors.append(
                    f"{script_path}:1: file is not canonically formatted; run --write"
                )
        except (
            ScriptFormatError,
            jsonschema.ValidationError,
            json.JSONDecodeError,
        ) as exc:
            line = getattr(exc, "line", 1)
            errors.append(f"{script_path}:{line}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check", action="store_true", help="validate without changing files"
    )
    mode.add_argument("--write", action="store_true", help="migrate and format files")
    parser.add_argument("path", type=pathlib.Path)
    args = parser.parse_args(argv)
    errors = process(args.path, write=args.write)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Checked {len(discover_scripts(args.path))} script(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
