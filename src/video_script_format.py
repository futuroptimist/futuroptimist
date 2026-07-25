"""Parse, validate, and canonically format Futuroptimist video scripts."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from jsonschema import Draft7Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "video_script.schema.json"
SOURCE_RE = re.compile(r"^> (Draft script|Transcript) for video `([^`]+)`$")
LEGACY_SOURCE_RE = re.compile(r"^> YouTube ID:\s*(\S+)\s*$")
TAG_RE = re.compile(r"^\[(NARRATOR|VISUAL)\]:\s*(.*)$")
TIMING_RE = re.compile(r"\s*<!--\s*(.*?)\s*->\s*(.*?)\s*-->\s*$")


class ScriptFormatError(ValueError):
    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.line = line


def parse_script(text: str, *, legacy: bool = False) -> dict:
    """Parse Markdown into the normalized object validated by the JSON schema."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        raise ScriptFormatError("expected a nonempty H1 title", 1)
    title = lines[0][2:].strip()
    source_index = next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip()), None
    )
    if source_index is None:
        raise ScriptFormatError("missing canonical source blockquote", 2)
    match = SOURCE_RE.match(lines[source_index])
    if not match and legacy:
        old = LEGACY_SOURCE_RE.match(lines[source_index])
        if old:
            kind, video_id = "draft", old.group(1)
        else:
            raise ScriptFormatError("invalid source blockquote", source_index + 1)
    elif match:
        kind = "draft" if match.group(1) == "Draft script" else "transcript"
        video_id = match.group(2).strip()
    else:
        raise ScriptFormatError("invalid source blockquote", source_index + 1)

    try:
        script_index = lines.index("## Script", source_index + 1)
    except ValueError as exc:
        raise ScriptFormatError("missing ## Script heading", source_index + 2) from exc

    outline: list[str] = []
    pre = lines[source_index + 1 : script_index]
    if any(line.strip() for line in pre):
        if legacy and any(line.strip() == "> Draft outline" for line in pre):
            outline = [
                line[1:].strip()
                for line in pre
                if line.startswith(">") and line.strip() != "> Draft outline"
            ]
            outline = [item for item in outline if item]
        else:
            nonblank = [
                (source_index + 2 + i, line) for i, line in enumerate(pre) if line
            ]
            if not nonblank or nonblank[0][1] != "## Outline":
                raise ScriptFormatError(
                    "expected optional ## Outline before ## Script", nonblank[0][0]
                )
            for number, line in nonblank[1:]:
                if not line.startswith("- ") or not line[2:].strip():
                    raise ScriptFormatError(
                        "outline entries must be nonempty '- ' items", number
                    )
                outline.append(line[2:].strip())

    segments = []
    for index, line in enumerate(lines[script_index + 1 :], script_index + 2):
        if not line:
            continue
        if line.startswith("### ") and line[4:].strip():
            segments.append({"type": "section", "text": line[4:].strip()})
            continue
        if legacy and line.startswith("> ") and line[2:].strip():
            segments.append({"type": "section", "text": line[2:].strip()})
            continue
        tag = TAG_RE.match(line)
        if not tag:
            raise ScriptFormatError(
                "script body must use ###, [NARRATOR]:, or [VISUAL]:", index
            )
        segment_type = tag.group(1).lower()
        value = tag.group(2)
        if not value.strip():
            raise ScriptFormatError(f"empty {segment_type} segment", index)
        segment = {"type": segment_type, "text": value}
        if segment_type == "narrator":
            timing = TIMING_RE.search(value)
            if timing:
                segment["timing"] = {"start": timing.group(1), "end": timing.group(2)}
        segments.append(segment)
    document = {
        "schema_version": 1,
        "title": title,
        "kind": kind,
        "video_id": video_id,
        "outline": outline,
        "segments": segments,
    }
    errors = sorted(
        Draft7Validator(json.loads(SCHEMA_PATH.read_text())).iter_errors(document),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ScriptFormatError(f"schema: {errors[0].message}")
    return document


def format_script(document: dict) -> str:
    source = "Draft script" if document["kind"] == "draft" else "Transcript"
    blocks = [
        f"# {document['title']}",
        f"> {source} for video `{document['video_id']}`",
    ]
    if document["outline"]:
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


def validate_metadata(document: dict, path: pathlib.Path) -> None:
    metadata_path = path.with_name("metadata.json")
    if not metadata_path.exists():
        return
    actual = str(json.loads(metadata_path.read_text()).get("youtube_id", "")).strip()
    if actual and document["video_id"] not in {actual, "draft", "<youtube_id>"}:
        raise ScriptFormatError(
            f"video id {document['video_id']!r} does not match metadata youtube_id {actual!r}",
            3,
        )


def discover(path: pathlib.Path) -> list[pathlib.Path]:
    return [path] if path.is_file() else sorted(path.rglob("script.md"))


def run(path: pathlib.Path, *, write: bool) -> int:
    failed = False
    for script in discover(path):
        try:
            original = script.read_text(encoding="utf-8")
            document = parse_script(original, legacy=write)
            validate_metadata(document, script)
            canonical = format_script(document)
            if canonical != original:
                if write:
                    script.write_text(canonical, encoding="utf-8")
                    print(f"formatted {script}")
                else:
                    raise ScriptFormatError("not canonically formatted")
        except (ScriptFormatError, json.JSONDecodeError) as exc:
            failed = True
            print(f"{script}:{getattr(exc, 'line', 1)}: {exc}", file=sys.stderr)
    return int(failed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("path", type=pathlib.Path)
    args = parser.parse_args(argv)
    return run(args.path, write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
