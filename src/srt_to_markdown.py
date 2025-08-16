import argparse
import html
import pathlib
import re
from typing import List, Tuple


def clean_srt_text(text: str) -> str:
    """Normalize SRT caption text for Markdown.

    Converts HTML tags like ``<i>``, ``<em>``, ``<b>``, ``<strong>`` (with optional
    attributes), and ``<br>`` to Markdown equivalents while stripping any other HTML
    tags. Tag matching is case-insensitive.
    Non-breaking spaces (``&nbsp;``) are converted to regular spaces.
    Speaker prefixes such as ``- [Narrator]`` are removed. Runs of whitespace are
    collapsed to a single space so downstream scripts see clean, predictable text.
    """

    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"^-?\s*\[[^\]]+\]\s*:?\s*", "", text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(i|em)\b[^>]*>", "*", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(b|strong)\b[^>]*>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"</?u\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[a-zA-Z/][^>]*>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_srt(path: pathlib.Path) -> List[Tuple[str, str, str]]:
    entries = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.isdigit():
            if i + 1 >= len(lines):
                break
            time_line = lines[i + 1].strip()
            match = re.match(
                r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
                time_line,
            )
            if not match:
                i += 1
                continue
            start, end = match.groups()
            i += 2
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            text = clean_srt_text(" ".join(text_lines))
            entries.append((start, end, text))
        else:
            i += 1
    return entries


def to_markdown(
    entries: List[Tuple[str, str, str]], title: str, youtube_id: str
) -> str:
    parts = []
    if title:
        parts.append(f"# {title}")
        parts.append("")
    if youtube_id:
        parts.append(f"> Draft script for video `{youtube_id}`")
        parts.append("")
    parts.append("## Script")
    parts.append("")
    for start, end, text in entries:
        parts.append(f"[NARRATOR]: {text}  <!-- {start} -> {end} -->")
        parts.append("")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert SRT captions to Futuroptimist script format"
    )
    parser.add_argument("srt", type=pathlib.Path)
    parser.add_argument("--title", default="", help="Video title")
    parser.add_argument("--youtube-id", default="", help="YouTube ID")
    parser.add_argument("-o", "--output", type=pathlib.Path)
    args = parser.parse_args()

    entries = parse_srt(args.srt)
    markdown = to_markdown(entries, args.title, args.youtube_id)

    if args.output:
        args.output.write_text(markdown)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
