"""Combine a video script's production Markdown files into a printable PDF."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from markdown_it import MarkdownIt
from markdown_it.token import Token
from weasyprint import CSS, HTML
from weasyprint.urls import default_url_fetcher

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEO_SCRIPTS = REPO_ROOT / "video_scripts"
CSS_PATH = REPO_ROOT / "assets" / "print" / "production.css"
DATED_SLUG = re.compile(r"^(\d{8})_")
MARKER = re.compile(r"^\[([ xX!\-])\](?:\s+|$)")


class ProductionPDFError(ValueError):
    """Raised for invalid production-plan selection or unsafe resources."""


@dataclass(frozen=True)
class RenderResult:
    requested_selector: str
    resolved_slug: str
    source_paths: tuple[str, ...]
    output_path: str


def _contained(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def production_files(directory: Path) -> list[Path]:
    """Return safe, direct Markdown files in a production directory."""
    if not directory.is_dir() or not _contained(directory, VIDEO_SCRIPTS):
        return []
    return sorted(
        (
            item
            for item in directory.iterdir()
            if item.is_file()
            and not item.is_symlink()
            and item.suffix.casefold() == ".md"
            and _contained(item, directory)
        ),
        key=lambda item: (item.name.casefold(), item.name),
    )


def discover_eligible(video_scripts: Path = VIDEO_SCRIPTS) -> list[str]:
    """Discover eligible direct child slugs in deterministic order."""
    if not video_scripts.is_dir():
        return []
    slugs = [
        child.name
        for child in video_scripts.iterdir()
        if child.is_dir()
        and not child.is_symlink()
        and _contained(child, video_scripts)
        and production_files_for_root(child / "production", video_scripts)
        and child.name.casefold() != "latest"
    ]
    return sorted(slugs, key=lambda slug: (slug.casefold(), slug))


def resolve_slug(selector: str, video_scripts: Path = VIDEO_SCRIPTS) -> str:
    """Validate an exact slug or dynamically resolve ``latest``."""
    eligible = discover_eligible(video_scripts)
    if selector == "latest":
        dated: list[tuple[datetime, str, str]] = []
        for slug in eligible:
            match = DATED_SLUG.match(slug)
            if not match:
                continue
            try:
                date = datetime.strptime(match.group(1), "%Y%m%d")
            except ValueError:
                continue
            dated.append((date, slug.casefold(), slug))
        if not dated:
            raise ProductionPDFError("no dated eligible video script exists")
        return max(dated)[2]
    if (
        not selector
        or Path(selector).is_absolute()
        or "/" in selector
        or "\\" in selector
        or selector in {".", ".."}
    ):
        raise ProductionPDFError(f"invalid video script selector: {selector!r}")
    if selector not in eligible:
        listing = "\n".join(f"  - {slug}" for slug in eligible) or "  (none)"
        raise ProductionPDFError(
            f"video script {selector!r} is not eligible; eligible slugs:\n{listing}"
        )
    selected = video_scripts / selector
    if selected.is_symlink() or not _contained(selected, video_scripts):
        raise ProductionPDFError(f"video script escapes video_scripts: {selector!r}")
    return selector


def ordered_sources(slug: str, video_scripts: Path = VIDEO_SCRIPTS) -> list[Path]:
    """Order direct production Markdown from valid links in footage.md."""
    production = video_scripts / slug / "production"
    files = production_files_for_root(production, video_scripts)
    if not files:
        raise ProductionPDFError(f"{slug!r} has no direct production Markdown files")
    by_name = {item.name: item for item in files}
    ordered: list[Path] = []
    footage = video_scripts / slug / "footage.md"
    if footage.is_file() and not footage.is_symlink():
        parser = MarkdownIt("commonmark", {"html": False})
        for token in parser.parse(footage.read_text(encoding="utf-8")):
            if token.type != "inline" or not token.children:
                continue
            for child in token.children:
                if child.type != "link_open":
                    continue
                href = child.attrGet("href") or ""
                parsed = urlparse(href)
                path = PurePosixPath(unquote(parsed.path))
                if parsed.scheme or parsed.netloc or path.is_absolute():
                    continue
                parts = path.parts
                if len(parts) != 2 or parts[0] != "production" or ".." in parts:
                    continue
                candidate = by_name.get(parts[1])
                if candidate is not None and candidate not in ordered:
                    ordered.append(candidate)
    ordered.extend(item for item in files if item not in ordered)
    return ordered


def production_files_for_root(directory: Path, video_scripts: Path) -> list[Path]:
    if not directory.is_dir() or not _contained(directory, video_scripts):
        return []
    return sorted(
        [
            item
            for item in directory.iterdir()
            if item.is_file()
            and not item.is_symlink()
            and item.suffix.casefold() == ".md"
            and _contained(item, directory)
        ],
        key=lambda item: (item.name.casefold(), item.name),
    )


def markdown_parser() -> MarkdownIt:
    parser = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")
    parser.core.ruler.after("inline", "production_status_markers", _status_markers)
    return parser


def _status_markers(state) -> None:
    """Convert markers only when they begin actual list-item inline content."""
    in_item = False
    for token in state.tokens:
        if token.type == "list_item_open":
            in_item = True
        elif token.type == "list_item_close":
            in_item = False
        elif in_item and token.type == "inline" and token.children:
            first = token.children[0]
            if first.type != "text":
                continue
            match = MARKER.match(first.content)
            if not match:
                continue
            status = {
                " ": "empty",
                "x": "checked",
                "X": "checked",
                "-": "progress",
                "!": "blocked",
            }[match.group(1)]
            first.content = first.content[match.end() :]
            marker = Token("html_inline", "", 0)
            marker.content = (
                f'<span class="status status-{status}" aria-label="{status}"></span>'
            )
            token.children.insert(0, marker)


def build_html(slug: str, sources: list[Path]) -> str:
    parser = markdown_parser()
    sections = []
    for source in sources:
        rendered = parser.render(source.read_text(encoding="utf-8"))
        sections.append(
            f'<section class="production-document" data-source="{source.name}">{rendered}</section>'
        )
    body = "\n".join(sections)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{slug} production checklist</title><meta name="author" content="Futuroptimist">
</head><body data-slug="{slug}">{body}</body></html>"""


def _safe_fetcher(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "file":
        raise ProductionPDFError(f"remote resources are disabled: {url}")
    path = Path(unquote(parsed.path))
    if not _contained(path, REPO_ROOT):
        raise ProductionPDFError(f"local resource escapes repository: {path}")
    return default_url_fetcher(url)


def render(
    selector: str,
    output: Path | None = None,
    page_size: str = "letter",
    *,
    video_scripts: Path = VIDEO_SCRIPTS,
) -> RenderResult:
    resolved = resolve_slug(selector, video_scripts)
    sources = ordered_sources(resolved, video_scripts)
    output = (
        output
        or REPO_ROOT
        / "dist"
        / "production-pdfs"
        / f"{resolved}-production-checklist.pdf"
    )
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    css = CSS(
        string=CSS_PATH.read_text(encoding="utf-8")
        + f'\n@page {{ size: {page_size}; @bottom-left {{ content: "{resolved}"; }} }}'
    )
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, suffix=".pdf", delete=False
        ) as handle:
            temporary = Path(handle.name)
        HTML(
            string=build_html(resolved, sources),
            base_url=REPO_ROOT.as_uri(),
            url_fetcher=_safe_fetcher,
        ).write_pdf(temporary, stylesheets=[css])
        if not temporary.read_bytes().startswith(b"%PDF-"):
            raise ProductionPDFError("renderer did not produce a PDF")
        temporary.replace(output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return RenderResult(
        selector,
        resolved,
        tuple(str(path.relative_to(REPO_ROOT)) for path in sources),
        str(output),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--page-size", choices=("letter", "a4"), default="letter")
    parser.add_argument("--list", action="store_true", dest="list_slugs")
    parser.add_argument("--metadata-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.list_slugs:
            eligible = discover_eligible()
            print("Eligible video scripts:")
            print("\n".join(eligible) if eligible else "(none)")
            print(f"latest -> {resolve_slug('latest')}")
            return 0
        if not args.slug:
            parser.error("--slug is required unless --list is used")
        result = render(args.slug, args.output, args.page_size)
        if args.metadata_output:
            args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
            args.metadata_output.write_text(
                json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8"
            )
        print(f"Requested video script: {result.requested_selector}")
        print(f"Resolved video script: {result.resolved_slug}")
        print("Included sources: " + ", ".join(result.source_paths))
        print(f"Wrote {result.output_path}")
        return 0
    except (OSError, ProductionPDFError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
