"""Parse, validate, and canonically format Futuroptimist video scripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "video_script.schema.json"
SOURCE_RE = re.compile(r"^> (Draft script|Transcript) for video `([^`]+)`$")
LEGACY_SOURCE_RE = re.compile(r"^> YouTube ID:\s*(\S+)\s*$")
TAG_RE = re.compile(r"^\[(NARRATOR|VISUAL)\]:\s?(.*)$")
TIMING_RE = re.compile(r"\s*<!--\s*(.*?)\s*-->\s*$")


class ScriptFormatError(ValueError):
    """An actionable script parsing or validation error."""

    def __init__(self, line: int, message: str):
        super().__init__(message)
        self.line = line


@dataclass
class ParsedScript:
    data: dict


def parse_script(text: str, *, migrate: bool = False) -> ParsedScript:
    """Parse Markdown into the normalized schema representation."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        raise ScriptFormatError(1, "expected one nonempty '# Video title' heading")
    title = lines[0][2:]
    source_index = next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip()), None
    )
    if source_index is None:
        raise ScriptFormatError(2, "missing canonical source blockquote")
    source = SOURCE_RE.fullmatch(lines[source_index])
    if source:
        kind = "draft" if source.group(1) == "Draft script" else "transcript"
        video_id = source.group(2)
    elif migrate and (legacy := LEGACY_SOURCE_RE.fullmatch(lines[source_index])):
        kind, video_id = "draft", legacy.group(1)
    else:
        raise ScriptFormatError(
            source_index + 1, "expected canonical Draft script or Transcript blockquote"
        )
    if not video_id.strip():
        raise ScriptFormatError(source_index + 1, "video identifier must not be empty")

    script_index = next(
        (i for i, line in enumerate(lines) if line == "## Script"), None
    )
    if script_index is None:
        raise ScriptFormatError(1, "missing '## Script' heading")
    outline: list[str] = []
    outline_index = next(
        (i for i, line in enumerate(lines) if line == "## Outline"), None
    )
    if outline_index is not None:
        if outline_index > script_index:
            raise ScriptFormatError(outline_index + 1, "Outline must precede Script")
        for i in range(outline_index + 1, script_index):
            line = lines[i]
            if not line:
                continue
            if not line.startswith("- ") or not line[2:].strip():
                raise ScriptFormatError(
                    i + 1, "outline entries must use '- nonempty text'"
                )
            outline.append(line[2:])
    elif migrate:
        between = lines[source_index + 1 : script_index]
        if any(line == "> Draft outline" for line in between):
            for line in between:
                if line.startswith("> ") and line != "> Draft outline":
                    value = line[2:].strip()
                    if value:
                        outline.append(value)
    elif any(line.strip() for line in lines[source_index + 1 : script_index]):
        line_no = source_index + 2
        raise ScriptFormatError(line_no, "unexpected content before '## Script'")

    segments: list[dict] = []
    for i in range(script_index + 1, len(lines)):
        line = lines[i]
        if not line:
            continue
        if line.startswith("### ") and line[4:].strip():
            segments.append({"type": "section", "text": line[4:]})
            continue
        if migrate and line.startswith("> ") and line[2:].strip():
            segments.append({"type": "section", "text": line[2:]})
            continue
        match = TAG_RE.fullmatch(line)
        if not match:
            raise ScriptFormatError(
                i + 1, "script body must be a section, [NARRATOR]:, or [VISUAL]: block"
            )
        segment_type = match.group(1).lower()
        value = match.group(2)
        if not value.strip():
            raise ScriptFormatError(i + 1, f"empty {segment_type} segment")
        segment: dict[str, str] = {"type": segment_type, "text": value}
        if segment_type == "narrator" and (timing := TIMING_RE.search(value)):
            segment["timing"] = timing.group(1)
        segments.append(segment)
    if not segments:
        raise ScriptFormatError(
            script_index + 1, "script must contain at least one segment"
        )
    data: dict = {
        "schema_version": "1.0",
        "title": title,
        "document_kind": kind,
        "video_id": video_id,
        "segments": segments,
    }
    if outline:
        data["outline"] = outline
    return ParsedScript(data)


def format_script(parsed: ParsedScript) -> str:
    """Render a parsed script in deterministic canonical Markdown."""
    data = parsed.data
    label = "Draft script" if data["document_kind"] == "draft" else "Transcript"
    blocks = [f"# {data['title']}", f"> {label} for video `{data['video_id']}`"]
    if data.get("outline"):
        blocks.extend(
            ["## Outline", "\n".join(f"- {item}" for item in data["outline"])]
        )
    blocks.append("## Script")
    for segment in data["segments"]:
        if segment["type"] == "section":
            blocks.append(f"### {segment['text']}")
        else:
            blocks.append(f"[{segment['type'].upper()}]: {segment['text']}")
    return "\n\n".join(blocks) + "\n"


def validate_script(path: Path, *, migrate: bool = False) -> tuple[ParsedScript, str]:
    text = path.read_text(encoding="utf-8")
    parsed = parse_script(text, migrate=migrate)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft7Validator(schema).iter_errors(parsed.data),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ScriptFormatError(1, f"schema: {errors[0].message}")
    metadata_path = path.with_name("metadata.json")
    if metadata_path.exists():
        metadata_id = str(
            json.loads(metadata_path.read_text(encoding="utf-8")).get("youtube_id", "")
        ).strip()
        if metadata_id and parsed.data["video_id"] not in {
            metadata_id,
            "draft",
            "<youtube_id>",
        }:
            raise ScriptFormatError(
                source_line(path),
                f"video identifier does not match metadata.json ({metadata_id})",
            )
    return parsed, text


def source_line(path: Path) -> int:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("> "):
            return number
    return 1


def discover_scripts(path: Path) -> list[Path]:
    return [path] if path.is_file() else sorted(path.rglob("script.md"))


def run(paths: list[Path], *, write: bool) -> int:
    failed = False
    for path in paths:
        try:
            parsed, original = validate_script(path, migrate=write)
            canonical = format_script(parsed)
            if write:
                if canonical != original:
                    path.write_text(canonical, encoding="utf-8")
                    print(f"formatted {path}")
            elif canonical != original:
                raise ScriptFormatError(
                    1, "file is not canonically formatted; run with --write"
                )
        except (ScriptFormatError, json.JSONDecodeError) as exc:
            failed = True
            print(f"{path}:{getattr(exc, 'line', 1)}: {exc}", file=sys.stderr)
    return int(failed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    return run(discover_scripts(args.path), write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
