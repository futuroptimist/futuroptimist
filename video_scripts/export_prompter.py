"""Export canonical video narration as plain-text Prompter chapters."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.video_script_format import parse_script  # noqa: E402

PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")


def plain_text(text: str) -> str:
    """Remove non-spoken Markdown without changing the words."""
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"!?(?:\[([^]]+)\])\([^)]*\)", r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"(\*\*|__|\*|_)(.+?)\1", r"\2", text)
    return re.sub(r"\s+", " ", text).strip()


def chapters(document: dict) -> list[str]:
    narrators = [
        segment for segment in document["segments"] if segment["type"] == "narrator"
    ]
    if not any(segment["type"] == "visual" for segment in document["segments"]):
        return [plain_text(segment["text"]) for segment in narrators]
    result: list[str] = []
    pending: list[str] = []
    for segment in document["segments"]:
        if segment["type"] == "narrator":
            pending.append(plain_text(segment["text"]))
        elif segment["type"] == "visual" and pending:
            result.append(" ".join(pending))
            pending = []
    if pending:
        result.append(" ".join(pending))
    return result


def export(
    script: pathlib.Path, output: pathlib.Path, *, allow_placeholders: bool
) -> int:
    document = parse_script(script.read_text(encoding="utf-8"))
    content = "\n\n".join(chapters(document)) + "\n"
    unresolved = sorted(set(PLACEHOLDER_RE.findall(content)))
    if unresolved and not allow_placeholders:
        print("Unresolved placeholders:", file=sys.stderr)
        for placeholder in unresolved:
            print(f"- {placeholder}", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output} ({len(chapters(document))} chapters)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--slug")
    source.add_argument("--script", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args(argv)
    script = args.script or ROOT / "video_scripts" / args.slug / "script.md"
    output = args.output or script.parent / "prompter.txt"
    return export(script, output, allow_placeholders=args.allow_placeholders)


if __name__ == "__main__":
    raise SystemExit(main())
