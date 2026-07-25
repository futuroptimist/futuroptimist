"""Export canonical video narration as plain-text Prompter chapters."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.video_script_format import ScriptFormatError, parse_script  # noqa: E402

COMMENT_RE = re.compile(r"\s*<!--.*?-->\s*")
LINK_RE = re.compile(r"!?\[([^]]+)]\([^)]*\)")
PLACEHOLDER_RE = re.compile(r"<[^<>]+>")


def plain_text(text: str) -> str:
    """Remove Markdown presentation syntax without changing spoken words."""
    text = COMMENT_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"(?<!\\)[*_~]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_chapters(data: dict) -> tuple[list[str], int]:
    """Return visual-aligned chapters (or one chapter per transcript segment)."""
    narrators = [
        segment for segment in data["segments"] if segment["type"] == "narrator"
    ]
    has_visuals = any(segment["type"] == "visual" for segment in data["segments"])
    if not has_visuals:
        return [plain_text(segment["text"]) for segment in narrators], len(narrators)
    chapters: list[str] = []
    pending: list[str] = []
    for segment in data["segments"]:
        if segment["type"] == "narrator":
            pending.append(plain_text(segment["text"]))
        elif segment["type"] == "visual" and pending:
            chapters.append(" ".join(pending))
            pending = []
    if pending:
        chapters.append(" ".join(pending))
    return chapters, len(narrators)


def export(
    script: Path, output: Path, *, allow_placeholders: bool = False
) -> tuple[int, int]:
    parsed = parse_script(script.read_text(encoding="utf-8"))
    chapters, narrator_count = build_chapters(parsed.data)
    content = "\n\n".join(chapters) + "\n"
    placeholders = sorted(set(PLACEHOLDER_RE.findall(content)))
    if placeholders and not allow_placeholders:
        raise ValueError("unresolved placeholders: " + ", ".join(placeholders))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return len(chapters), narrator_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--slug")
    inputs.add_argument("--script", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args(argv)
    script = args.script or REPO_ROOT / "video_scripts" / args.slug / "script.md"
    script = script.resolve()
    output = (args.output or script.parent / "prompter.txt").resolve()
    try:
        chapters, _ = export(script, output, allow_placeholders=args.allow_placeholders)
    except (OSError, ValueError, ScriptFormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {output} ({chapters} chapters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
