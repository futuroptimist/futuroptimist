"""Combine an episode's production Markdown into a printable PDF."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from markdown_it import MarkdownIt
from markdown_it.token import Token
from weasyprint import CSS, HTML

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEO_SCRIPTS = REPO_ROOT / "video_scripts"
STYLESHEET = REPO_ROOT / "assets" / "print" / "production.css"
DATED_SLUG = re.compile(r"^(\d{8})_")
MARKER = re.compile(r"^\[([ xX!\-])\](?:\s+|$)")
LINK = re.compile(r"\[[^]]*\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")


class ProductionPDFError(ValueError):
    """Raised for invalid production-plan input."""


@dataclass(frozen=True)
class RenderResult:
    requested: str
    resolved_slug: str
    sources: tuple[str, ...]
    output: str


def _contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except (OSError, ValueError):
        return False
    return True


def production_files(
    directory: Path, video_scripts: Path = VIDEO_SCRIPTS
) -> list[Path]:
    if (
        not directory.is_dir()
        or directory.is_symlink()
        or not _contained(directory, video_scripts)
    ):
        return []
    return sorted(
        (
            path
            for path in directory.glob("*.md")
            if path.is_file() and not path.is_symlink()
        ),
        key=lambda path: (path.name.casefold(), path.name),
    )


def discover_eligible(video_scripts: Path = VIDEO_SCRIPTS) -> list[str]:
    root = video_scripts.resolve()
    eligible = []
    for child in video_scripts.iterdir() if video_scripts.is_dir() else ():
        if child.is_dir() and not child.is_symlink() and _contained(child, root):
            production = child / "production"
            if production_files(production, video_scripts):
                eligible.append(child.name)
    return sorted(eligible, key=lambda slug: (slug.casefold(), slug))


def resolve_slug(selector: str, video_scripts: Path = VIDEO_SCRIPTS) -> str:
    eligible = discover_eligible(video_scripts)
    if selector == "latest":
        candidates = []
        for slug in eligible:
            match = DATED_SLUG.match(slug)
            if match:
                try:
                    date = dt.datetime.strptime(match.group(1), "%Y%m%d").date()
                except ValueError:
                    continue
                candidates.append((date, slug.casefold(), slug))
        if not candidates:
            raise ProductionPDFError("no dated eligible production directories exist")
        return max(candidates)[2]
    if not selector or Path(selector).is_absolute() or selector in {".", ".."}:
        valid = False
    else:
        valid = "/" not in selector and "\\" not in selector and selector in eligible
    if not valid:
        listing = "\n".join(f"  {slug}" for slug in eligible) or "  (none)"
        raise ProductionPDFError(
            f"invalid or ineligible video script: {selector!r}\nEligible slugs:\n{listing}"
        )
    selected = video_scripts / selector
    if selected.is_symlink() or not _contained(selected, video_scripts):
        raise ProductionPDFError(f"video script escapes video_scripts: {selector!r}")
    return selector


def ordered_sources(slug: str, video_scripts: Path = VIDEO_SCRIPTS) -> list[Path]:
    episode = video_scripts / slug
    production = episode / "production"
    files = production_files(production, video_scripts)
    if not files:
        raise ProductionPDFError(
            f"production directory is missing or empty for {slug!r}"
        )
    by_name = {path.name: path for path in files}
    ordered: list[Path] = []
    footage = episode / "footage.md"
    if footage.is_file() and not footage.is_symlink():
        for raw in LINK.findall(footage.read_text(encoding="utf-8")):
            parsed = urlparse(unquote(raw))
            candidate = Path(parsed.path)
            if parsed.scheme or parsed.netloc or candidate.is_absolute():
                continue
            parts = candidate.parts
            if len(parts) != 2 or parts[0] != "production":
                continue
            matched = by_name.get(parts[1])
            if matched is not None and matched not in ordered:
                ordered.append(matched)
    ordered.extend(path for path in files if path not in ordered)
    return ordered


def _task_markers(state) -> None:
    tokens = state.tokens
    list_depth = 0
    for index, token in enumerate(tokens):
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            list_depth += 1
        elif token.type in {"bullet_list_close", "ordered_list_close"}:
            list_depth -= 1
        elif (
            token.type == "inline"
            and list_depth
            and index
            and tokens[index - 1].type == "paragraph_open"
        ):
            if not token.children or token.children[0].type != "text":
                continue
            match = MARKER.match(token.children[0].content)
            if not match:
                continue
            state_name = {
                " ": "empty",
                "x": "checked",
                "X": "checked",
                "-": "progress",
                "!": "blocked",
            }[match.group(1)]
            marker = Token("html_inline", "", 0)
            marker.content = f'<span class="status-box status-{state_name}" aria-label="{state_name}"></span>'
            token.children[0].content = token.children[0].content[match.end() :]
            token.children.insert(0, marker)
            for previous in reversed(tokens[:index]):
                if previous.type == "list_item_open":
                    previous.attrJoin("class", "task-list-item")
                    break


def markdown_renderer() -> MarkdownIt:
    renderer = MarkdownIt(
        "commonmark", {"html": False, "linkify": True, "typographer": True}
    ).enable("table")
    renderer.core.ruler.after("inline", "production_task_markers", _task_markers)
    return renderer


def build_html(slug: str, sources: list[Path]) -> str:
    renderer = markdown_renderer()
    sections = []
    for source in sources:
        sections.append(
            f'<section class="production-document" data-source="{source.name}">{renderer.render(source.read_text(encoding="utf-8"))}</section>'
        )
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<title>{slug} production checklist</title></head>"
        f'<body><div class="production-slug">{slug}</div>{"".join(sections)}</body></html>'
    )


def render(
    selector: str,
    output: Path | None = None,
    page_size: str = "letter",
    video_scripts: Path = VIDEO_SCRIPTS,
) -> RenderResult:
    slug = resolve_slug(selector, video_scripts)
    sources = ordered_sources(slug, video_scripts)
    output = (
        output
        or REPO_ROOT / "dist" / "production-pdfs" / f"{slug}-production-checklist.pdf"
    )
    output = Path(str(output).replace("{slug}", slug))
    output.parent.mkdir(parents=True, exist_ok=True)
    html = build_html(slug, sources).replace("<html>", f'<html class="{page_size}">', 1)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", dir=output.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        HTML(
            string=html,
            base_url=str(REPO_ROOT),
            url_fetcher=lambda url: (_ for _ in ()).throw(
                ProductionPDFError(f"resources disabled: {url}")
            ),
        ).write_pdf(temporary, stylesheets=[CSS(filename=STYLESHEET)])
        if not temporary.read_bytes().startswith(b"%PDF-"):
            raise ProductionPDFError("renderer did not create a PDF")
        temporary.replace(output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return RenderResult(
        selector,
        slug,
        tuple(str(path.relative_to(REPO_ROOT)) for path in sources),
        str(output),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--page-size", choices=("letter", "a4"), default="letter")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--report-json", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.list:
            eligible = discover_eligible()
            print("Eligible video scripts:")
            print("\n".join(eligible) if eligible else "(none)")
            print(f"latest -> {resolve_slug('latest')}")
            return 0
        if not args.slug:
            parser.error("--slug is required unless --list is used")
        result = render(args.slug, args.output, args.page_size)
        if args.report_json:
            args.report_json.parent.mkdir(parents=True, exist_ok=True)
            args.report_json.write_text(
                json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8"
            )
        print(f"Requested video script: {result.requested}")
        print(f"Resolved video script: {result.resolved_slug}")
        print("Included sources:")
        print("\n".join(f"- {source}" for source in result.sources))
        print(f"Wrote {result.output}")
        return 0
    except (OSError, ProductionPDFError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
