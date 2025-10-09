import argparse
import html
import json
import pathlib
import re
from typing import List, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


_ABBREV_RE = re.compile(
    r"(?:^|[\s(])(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|Mt|Gen|Capt|Sgt|Col|Lt|Maj|etc|e\.g|i\.e|vs)\.$",
    re.IGNORECASE,
)
_CLOSERS = "\"')]}»”’'"


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


def _timestamp_to_ms(ts: str) -> int:
    """Convert ``HH:MM:SS,mmm`` string into milliseconds."""
    hours, minutes, sec_ms = ts.split(":")
    seconds, millis = sec_ms.split(",")
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def parse_srt(path: pathlib.Path) -> List[Tuple[str, str, str]]:
    """Parse ``path`` into a list of ``(start, end, text)`` tuples.

    Sequence numbers are optional – segments may start directly with the time
    range. Lines that resolve to an empty string after :func:`clean_srt_text`
    are skipped. This filters out non-dialog captions such as ``[Music]`` or
    ``[Applause]`` so downstream scripts see only spoken narration.
    """

    entries = []
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    # Support captions exceeding 99 hours by allowing multi-digit hour fields.
    time_re = r"(\d{2,}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2,}:\d{2}:\d{2},\d{3})"
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
            match = re.match(time_re, time_line)
            if not match:
                i += 1
                continue
            i += 2
        else:
            match = re.match(time_re, line)
            if not match:
                i += 1
                continue
            i += 1
        start, end = match.groups()
        text_lines = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        text = clean_srt_text(" ".join(text_lines))
        # Compare timestamps numerically to handle captions spanning the 99h boundary
        if text and _timestamp_to_ms(start) < _timestamp_to_ms(end):
            entries.append((start, end, text))
    return entries


def _split_sentences(text: str) -> List[str]:
    sentences: List[str] = []
    start = 0
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch in ".!?":
            candidate = text[start : i + 1]
            if _ABBREV_RE.search(candidate):
                i += 1
                continue
            while i + 1 < length and text[i + 1] in _CLOSERS:
                i += 1
                candidate = text[start : i + 1]
            sentence = candidate.strip()
            if sentence:
                sentences.append(sentence)
            i += 1
            while i < length and text[i].isspace():
                i += 1
            start = i
        else:
            i += 1
    if start < length:
        tail = text[start:].strip()
        if tail:
            sentences.append(tail)
    return sentences if sentences else ([text.strip()] if text.strip() else [])


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
        for sentence in _split_sentences(text):
            parts.append(f"[NARRATOR]: {sentence}  <!-- {start} -> {end} -->")
            parts.append("")
    return "\n".join(parts)


def generate_script_for_slug(
    slug: str,
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    overwrite: bool = True,
    output: pathlib.Path | None = None,
) -> tuple[pathlib.Path, bool]:
    """Build ``script.md`` for ``slug`` using the stored metadata and subtitles.

    Returns a tuple of ``(path, created)`` where ``created`` is ``True`` when a
    new file was written. When ``overwrite`` is ``False`` and the target file
    already exists the function leaves it untouched and returns ``False`` for the
    ``created`` flag so callers can report that nothing changed.
    """

    repo_root = repo_root.resolve()
    slug_dir = repo_root / "video_scripts" / slug
    if not slug_dir.is_dir():
        raise FileNotFoundError(f"Missing video script directory for slug {slug!r}")
    metadata_path = slug_dir / "metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - validated in tests
        raise FileNotFoundError(
            f"Missing metadata.json for slug {slug!r}: {metadata_path}"
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid JSON in {metadata_path}: {exc}") from exc
    youtube_id = str(metadata.get("youtube_id", "")).strip()
    if not youtube_id:
        raise ValueError(f"metadata for {slug!r} is missing a youtube_id")
    title = str(metadata.get("title", "")).strip()
    subtitles_path = repo_root / "subtitles" / f"{youtube_id}.srt"
    if not subtitles_path.exists():
        raise FileNotFoundError(
            f"Subtitle file not found for {youtube_id}: {subtitles_path}"
        )
    if output is None:
        output_path = slug_dir / "script.md"
    else:
        output_path = pathlib.Path(output)
        if not output_path.is_absolute():
            output_path = (repo_root / output_path).resolve()
    if output_path.exists() and not overwrite:
        return output_path, False

    entries = parse_srt(subtitles_path)
    markdown = to_markdown(entries, title, youtube_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    return output_path, True


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Convert SRT captions to Futuroptimist script format"
    )
    parser.add_argument("srt", nargs="?", type=pathlib.Path)
    parser.add_argument("--title", default="", help="Video title")
    parser.add_argument("--youtube-id", default="", help="YouTube ID")
    parser.add_argument("-o", "--output", type=pathlib.Path)
    parser.add_argument(
        "--slug",
        default=None,
        help="Video slug like YYYYMMDD_slug to read metadata & subtitles",
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=REPO_ROOT,
        help="Repository root (used with --slug)",
    )
    overwrite_group = parser.add_mutually_exclusive_group()
    overwrite_group.add_argument(
        "--overwrite",
        dest="overwrite",
        action="store_true",
        help="Overwrite existing script when using --slug (default)",
    )
    overwrite_group.add_argument(
        "--no-overwrite",
        dest="overwrite",
        action="store_false",
        help="Fail if the output exists when using --slug",
    )
    parser.set_defaults(overwrite=True)
    args = parser.parse_args(argv)

    if args.slug:
        path, created = generate_script_for_slug(
            args.slug,
            repo_root=args.repo_root,
            overwrite=args.overwrite,
            output=args.output,
        )
        if created:
            print(f"Wrote {path}")
        else:
            print(f"Skipped existing {path}")
        return

    if args.srt is None:
        parser.error("SRT path is required unless --slug is provided")

    entries = parse_srt(args.srt)
    markdown = to_markdown(entries, args.title, args.youtube_id)

    if args.output:
        args.output.write_text(markdown)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
