"""Combine an episode's production Markdown files into a printable PDF."""

from __future__ import annotations

import argparse
import html as html_module
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token
from weasyprint import CSS, HTML

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEO_SCRIPTS = REPO_ROOT / "video_scripts"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "dist" / "production-pdfs"
STYLESHEET = REPO_ROOT / "assets" / "print" / "production.css"
DATED_SLUG = re.compile(r"^(\d{8})_")
STATUS_MARKERS = {
    " ": "empty",
    "x": "checked",
    "X": "checked",
    "-": "progress",
    "!": "blocked",
}


class ProductionPDFError(ValueError):
    """Raised for invalid production-plan input."""


@dataclass(frozen=True)
class RenderResult:
    requested: str
    resolved_slug: str
    sources: tuple[str, ...]
    output: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def _contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except (OSError, ValueError):
        return False
    return True


def production_files(slug_dir: Path, video_scripts: Path = VIDEO_SCRIPTS) -> list[Path]:
    """Return safe, direct Markdown files for one slug."""
    root = video_scripts.resolve()
    if not _contained(slug_dir, root) or not slug_dir.is_dir():
        return []
    production = slug_dir / "production"
    if not production.is_dir() or not _contained(production, root):
        return []
    files = []
    for path in production.iterdir():
        if (
            path.suffix.casefold() == ".md"
            and path.is_file()
            and _contained(path, production)
        ):
            files.append(path)
    return sorted(files, key=lambda path: (path.name.casefold(), path.name))


def discover_eligible(video_scripts: Path = VIDEO_SCRIPTS) -> list[str]:
    """Discover eligible direct slug directories in deterministic order."""
    if not video_scripts.is_dir():
        return []
    slugs = [
        child.name
        for child in video_scripts.iterdir()
        if child.is_dir() and production_files(child, video_scripts)
    ]
    return sorted(slugs, key=lambda slug: (slug.casefold(), slug))


def _eligible_message(eligible: list[str]) -> str:
    listing = "\n".join(f"  - {slug}" for slug in eligible) or "  (none)"
    return f"Eligible video scripts:\n{listing}"


def resolve_slug(selector: str, video_scripts: Path = VIDEO_SCRIPTS) -> str:
    """Resolve ``latest`` or validate an exact eligible slug."""
    eligible = discover_eligible(video_scripts)
    if selector == "latest":
        dated = []
        for slug in eligible:
            match = DATED_SLUG.match(slug)
            if not match:
                continue
            try:
                date = datetime.strptime(match.group(1), "%Y%m%d").date()
            except ValueError:
                continue
            dated.append((date, slug.casefold(), slug))
        if not dated:
            raise ProductionPDFError(
                "latest requires at least one eligible YYYYMMDD_slug directory.\n"
                + _eligible_message(eligible)
            )
        return max(dated)[2]
    candidate = Path(selector)
    if (
        not selector
        or candidate.is_absolute()
        or selector in {".", ".."}
        or "/" in selector
        or "\\" in selector
    ):
        raise ProductionPDFError(
            f"invalid video script selector: {selector!r}\n{_eligible_message(eligible)}"
        )
    if selector not in eligible:
        raise ProductionPDFError(
            f"video script is not eligible: {selector!r}\n{_eligible_message(eligible)}"
        )
    slug_dir = video_scripts / selector
    if not _contained(slug_dir, video_scripts):
        raise ProductionPDFError(f"video script escapes video_scripts: {selector!r}")
    return selector


def ordered_sources(slug: str, video_scripts: Path = VIDEO_SCRIPTS) -> list[Path]:
    """Order direct production Markdown using safe links in footage.md first."""
    slug_dir = video_scripts / slug
    files = production_files(slug_dir, video_scripts)
    if not files:
        raise ProductionPDFError(
            f"video script has no direct production Markdown files: {slug}"
        )
    by_name = {path.name: path for path in files}
    ordered: list[Path] = []
    footage = slug_dir / "footage.md"
    if footage.is_file() and _contained(footage, slug_dir):
        parser = MarkdownIt("commonmark", {"html": False})
        for token in parser.parse(footage.read_text(encoding="utf-8")):
            children = token.children or []
            for child in children:
                if child.type != "link_open":
                    continue
                href = unquote(child.attrGet("href") or "")
                parsed = urlsplit(href)
                parts = Path(parsed.path).parts
                if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
                    continue
                if len(parts) != 2 or parts[0] != "production":
                    continue
                source = by_name.get(parts[1])
                if source is not None and source not in ordered:
                    ordered.append(source)
    ordered.extend(path for path in files if path not in ordered)
    return ordered


def _status_rule(state):
    tokens = state.tokens
    for index, token in enumerate(tokens):
        if (
            token.type != "inline"
            or index == 0
            or tokens[index - 1].type != "paragraph_open"
        ):
            continue
        list_index = index - 2
        if (
            list_index < 0
            or tokens[list_index].type != "list_item_open"
            or not token.children
        ):
            continue
        first = token.children[0]
        match = (
            re.match(r"^\[([ xX!\-])\](?:\s+|$)", first.content)
            if first.type == "text"
            else None
        )
        if not match:
            continue
        status = STATUS_MARKERS[match.group(1)]
        first.content = first.content[match.end() :]
        marker = Token("html_inline", "", 0)
        marker.content = (
            f'<span class="status status-{status}" aria-label="{status}"></span>'
        )
        token.children.insert(0, marker)
        tokens[list_index].attrSet("class", f"task task-{status}")


def markdown_parser() -> MarkdownIt:
    parser = MarkdownIt(
        "commonmark", {"html": False, "linkify": False, "typographer": False}
    )
    parser.enable("table")
    parser.core.ruler.after("inline", "production_status", _status_rule)
    return parser


def build_html(slug: str, sources: list[Path], repo_root: Path = REPO_ROOT) -> str:
    """Render safe Markdown into one semantic HTML section per source."""
    parser = markdown_parser()
    sections = []
    for source in sources:
        body = parser.render(source.read_text(encoding="utf-8"))
        name = html_module.escape(source.name, quote=True)
        sections.append(
            f'<section class="production-document" data-source="{name}">{body}</section>'
        )
    safe_slug = html_module.escape(slug, quote=True)
    title = f"{safe_slug} production checklist"
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<title>{title}</title><meta name="author" content="Futuroptimist">'
        f'<meta name="subject" content="{safe_slug}"></head>'
        f'<body data-slug="{safe_slug}">{"".join(sections)}</body></html>'
    )


def _deny_resources(url: str):
    raise ProductionPDFError(f"external and embedded resources are disabled: {url}")


def default_output(slug: str, repo_root: Path = REPO_ROOT) -> Path:
    return repo_root / "dist" / "production-pdfs" / f"{slug}-production-checklist.pdf"


def render_pdf(
    selector: str,
    output: Path | None = None,
    page_size: str = "letter",
    *,
    repo_root: Path = REPO_ROOT,
) -> RenderResult:
    """Resolve, render, and atomically publish a production PDF."""
    if page_size not in {"letter", "a4"}:
        raise ProductionPDFError(f"unsupported page size: {page_size}")
    video_scripts = repo_root / "video_scripts"
    slug = resolve_slug(selector, video_scripts)
    sources = ordered_sources(slug, video_scripts)
    destination = output or default_output(slug, repo_root)
    destination = destination if destination.is_absolute() else repo_root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = build_html(slug, sources, repo_root)
    page_css = f'@page {{ size: {"Letter" if page_size == "letter" else "A4"}; }}'
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, suffix=".pdf", delete=False
        ) as handle:
            temporary = Path(handle.name)
        HTML(string=html, url_fetcher=_deny_resources).write_pdf(
            temporary,
            stylesheets=[
                CSS(filename=repo_root / "assets" / "print" / "production.css"),
                CSS(string=page_css),
            ],
            presentational_hints=False,
        )
        if temporary.stat().st_size == 0:
            raise ProductionPDFError("renderer produced an empty PDF")
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return RenderResult(
        requested=selector,
        resolved_slug=slug,
        sources=tuple(str(path.relative_to(repo_root)) for path in sources),
        output=str(
            destination.relative_to(repo_root)
            if _contained(destination, repo_root)
            else destination
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--page-size", choices=("letter", "a4"), default="letter")
    parser.add_argument("--list", action="store_true", dest="list_slugs")
    parser.add_argument("--result-json", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.list_slugs:
        eligible = discover_eligible()
        print(_eligible_message(eligible))
        try:
            print(f"latest -> {resolve_slug('latest')}")
        except ProductionPDFError as error:
            print(f"latest -> unavailable ({str(error).splitlines()[0]})")
        return 0
    if not args.slug:
        parser.error("--slug is required unless --list is used")
    try:
        result = render_pdf(args.slug, args.output, args.page_size)
        if args.result_json:
            args.result_json.parent.mkdir(parents=True, exist_ok=True)
            args.result_json.write_text(result.to_json() + "\n", encoding="utf-8")
    except (OSError, ProductionPDFError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Requested video script: {result.requested}")
    print(f"Resolved video script: {result.resolved_slug}")
    print("Included sources:")
    for source in result.sources:
        print(f"  - {source}")
    print(f"Wrote {result.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
