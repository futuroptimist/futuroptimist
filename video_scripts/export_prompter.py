"""Export canonical video narration as plain-text Prompter chapters."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.video_script_format import parse_script, validate_script  # noqa: E402

PLACEHOLDER_RE = re.compile(r"<[^<>\n]+>")
COMMENT_RE = re.compile(r"<!--.*?-->")
LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^)]*\)")


def plain_text(text: str) -> str:
    """Remove Markdown-only notation while retaining its readable words."""

    text = COMMENT_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"(?<!\\)(\*\*|__|\*|_|~~)", "", text)
    return " ".join(text.split())


def build_chapters(segments: list[dict]) -> tuple[list[str], int]:
    """Return Prompter chapters and the count of included narrator segments."""

    has_visuals = any(segment["type"] == "visual" for segment in segments)
    narrators = [segment for segment in segments if segment["type"] == "narrator"]
    if not has_visuals:
        return [plain_text(segment["text"]) for segment in narrators], len(narrators)
    chapters: list[str] = []
    pending: list[str] = []
    count = 0
    for segment in segments:
        if segment["type"] == "narrator":
            pending.append(plain_text(segment["text"]))
            count += 1
        elif segment["type"] == "visual" and pending:
            chapters.append(" ".join(pending))
            pending = []
    if pending:
        chapters.append(" ".join(pending))
    return chapters, count


def export_prompter(
    script_path: pathlib.Path,
    output_path: pathlib.Path,
    *,
    allow_placeholders: bool = False,
) -> tuple[int, int]:
    """Validate and export a script atomically enough to avoid failed artifacts."""

    parsed = parse_script(script_path.read_text(encoding="utf-8"))
    validate_script(parsed, script_path)
    chapters, narrator_count = build_chapters(parsed.segments)
    output = "\n\n".join(chapters) + "\n"
    placeholders = sorted(set(PLACEHOLDER_RE.findall(output)))
    if placeholders and not allow_placeholders:
        raise ValueError("unresolved placeholders: " + ", ".join(placeholders))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    return len(chapters), narrator_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--slug", help="folder under video_scripts")
    source.add_argument("--script", type=pathlib.Path, help="explicit script.md path")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args(argv)
    script_path = args.script or REPO_ROOT / "video_scripts" / args.slug / "script.md"
    output_path = args.output or script_path.parent / "prompter.txt"
    try:
        chapters, _ = export_prompter(
            script_path, output_path, allow_placeholders=args.allow_placeholders
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {output_path} ({chapters} chapters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
