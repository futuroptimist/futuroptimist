"""Export canonical video narration as plain-text Prompter chapters."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.video_script_format import (  # noqa: E402
    ScriptFormatError,
    parse_script,
    validate_document,
)

PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
COMMENT_RE = re.compile(r"<!--.*?-->")
LINK_RE = re.compile(r"!?\[([^]]+)\]\([^)]+\)")


def plain_text(text: str) -> str:
    """Remove non-spoken Markdown while retaining its visible text."""
    text = COMMENT_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"(?<!\w)(\*\*|__)(?=\S)(.+?)(?<=\S)\1(?!\w)", r"\2", text)
    text = re.sub(r"(?<!\w)(\*|_)(?=\S)(.+?)(?<=\S)\1(?!\w)", r"\2", text)
    text = re.sub(r"(?<!~)~~(?=\S)(.+?)(?<=\S)~~(?!~)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def build_chapters(document: dict) -> tuple[list[str], int]:
    narrators = [
        segment for segment in document["segments"] if segment["type"] == "narrator"
    ]
    if not any(segment["type"] == "visual" for segment in document["segments"]):
        return [plain_text(segment["text"]) for segment in narrators], len(narrators)
    chapters: list[str] = []
    current: list[str] = []
    count = 0
    for segment in document["segments"]:
        if segment["type"] == "narrator":
            current.append(plain_text(segment["text"]))
            count += 1
        elif segment["type"] == "visual" and current:
            chapters.append(" ".join(current))
            current = []
    if current:
        chapters.append(" ".join(current))
    return chapters, count


def export(
    script: Path, output: Path, *, allow_placeholders: bool = False
) -> tuple[int, int]:
    document = parse_script(script.read_text(encoding="utf-8"))
    validate_document(document)
    chapters, narrator_count = build_chapters(document)
    empty_narrators = [
        segment
        for segment in document["segments"]
        if segment["type"] == "narrator" and not plain_text(segment["text"])
    ]
    if empty_narrators:
        raise ValueError("narration is empty after removing non-spoken Markdown")
    rendered = "\n\n".join(chapters) + "\n"
    placeholders = sorted(set(PLACEHOLDER_RE.findall(rendered)))
    if placeholders and not allow_placeholders:
        raise ValueError("unresolved placeholders: " + ", ".join(placeholders))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        temporary.replace(output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(chapters), narrator_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--slug")
    source.add_argument("--script", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args(argv)
    script = args.script or REPO_ROOT / "video_scripts" / args.slug / "script.md"
    output = args.output or script.parent / "prompter.txt"
    try:
        chapters, _ = export(script, output, allow_placeholders=args.allow_placeholders)
    except (OSError, ValueError, ScriptFormatError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output} ({chapters} chapters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
