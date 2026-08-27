"""Combine a video's production Markdown files into a printable PDF."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

from markdown_it import MarkdownIt
from weasyprint import CSS, HTML

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEO_SCRIPTS = REPO_ROOT / "video_scripts"
STYLESHEET = REPO_ROOT / "assets" / "print" / "production.css"
DATED_SLUG = re.compile(r"^(\d{8})_")
LINK = re.compile(r"\[[^]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
MARKER = re.compile(r"^\[([ xX!\-])\]\s+")


class ProductionPdfError(ValueError):
    """Raised when production inputs are invalid or unsafe."""


@dataclass(frozen=True)
class RenderResult:
    requested_selector: str
    resolved_slug: str
    included_sources: list[str]
    output_path: str


def _contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except (OSError, ValueError):
        return False
    return True


def production_files(
    directory: Path, video_scripts: Path = VIDEO_SCRIPTS
) -> list[Path]:
    """Return safe direct Markdown files from a production directory."""
    if not directory.is_dir() or not _contained(directory, video_scripts):
        return []
    return sorted(
        (
            path
            for path in directory.glob("*.md")
            if path.is_file() and not path.is_symlink() and _contained(path, directory)
        ),
        key=lambda path: (path.name.casefold(), path.name),
    )


def discover_eligible(video_scripts: Path = VIDEO_SCRIPTS) -> list[str]:
    """Discover eligible direct child slugs in deterministic order."""
    slugs = []
    for child in video_scripts.iterdir() if video_scripts.is_dir() else []:
        if (
            child.is_dir()
            and not child.is_symlink()
            and child.name != "latest"
            and _contained(child, video_scripts)
            and production_files(child / "production", video_scripts)
        ):
            slugs.append(child.name)
    return sorted(slugs, key=lambda slug: (slug.casefold(), slug))


def resolve_slug(selector: str, video_scripts: Path = VIDEO_SCRIPTS) -> str:
    eligible = discover_eligible(video_scripts)
    if selector != "latest":
        if (
            not selector
            or Path(selector).is_absolute()
            or "/" in selector
            or "\\" in selector
            or selector in {".", ".."}
            or selector not in eligible
        ):
            listing = "\n".join(f"  - {slug}" for slug in eligible) or "  (none)"
            raise ProductionPdfError(
                f"invalid or ineligible video script {selector!r}. Eligible slugs:\n{listing}"
            )
        return selector
    dated: list[tuple[datetime, str, str]] = []
    for slug in eligible:
        match = DATED_SLUG.match(slug)
        if match:
            try:
                date = datetime.strptime(match.group(1), "%Y%m%d")
            except ValueError:
                continue
            dated.append((date, slug.casefold(), slug))
    if not dated:
        raise ProductionPdfError(
            "latest cannot be resolved: no dated eligible directory exists"
        )
    return max(dated)[2]


def ordered_sources(slug: str, video_scripts: Path = VIDEO_SCRIPTS) -> list[Path]:
    directory = (video_scripts / slug / "production").resolve()
    if not _contained(directory, video_scripts):
        raise ProductionPdfError("production directory escapes video_scripts")
    files = production_files(directory, video_scripts)
    if not files:
        raise ProductionPdfError(f"{slug!r} has no direct production Markdown files")
    by_name = {path.name: path for path in files}
    ordered: list[Path] = []
    footage = video_scripts / slug / "footage.md"
    if footage.is_file() and not footage.is_symlink():
        for target in LINK.findall(footage.read_text(encoding="utf-8")):
            pure = PurePosixPath(target.split("#", 1)[0])
            if (
                not pure.is_absolute()
                and len(pure.parts) == 2
                and pure.parts[0] == "production"
                and pure.parts[1] in by_name
                and by_name[pure.parts[1]] not in ordered
            ):
                ordered.append(by_name[pure.parts[1]])
    ordered.extend(path for path in files if path not in ordered)
    return ordered


def markdown_renderer() -> MarkdownIt:
    renderer = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable(
        "table"
    )

    def status_markers(state):
        for index, token in enumerate(state.tokens):
            if (
                token.type != "inline"
                or index == 0
                or state.tokens[index - 1].type != "paragraph_open"
            ):
                continue
            if not any(
                item.type == "list_item_open"
                for item in state.tokens[max(0, index - 2) : index]
            ):
                continue
            match = MARKER.match(token.content)
            if not match or not token.children:
                continue
            status = {
                " ": "empty",
                "x": "checked",
                "X": "checked",
                "-": "progress",
                "!": "blocked",
            }[match.group(1)]
            token.content = MARKER.sub("", token.content, count=1)
            first = token.children[0]
            if first.type == "text":
                first.content = MARKER.sub("", first.content, count=1)
                from markdown_it.token import Token

                box = Token("html_inline", "", 0)
                box.content = f'<span class="status status-{status}" aria-label="{status}"></span>'
                token.children.insert(0, box)

    renderer.core.ruler.after("inline", "production_status_markers", status_markers)
    return renderer


def build_html(slug: str, sources: list[Path]) -> str:
    md = markdown_renderer()
    sections = []
    for source in sources:
        body = md.render(source.read_text(encoding="utf-8"))
        sections.append(
            f'<section class="production-document" data-source="{html.escape(source.name)}">{body}</section>'
        )
    title = f"{slug} production checklist"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title></head><body data-slug='{html.escape(slug)}'>{''.join(sections)}</body></html>"


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
    css = STYLESHEET.read_text(encoding="utf-8") + f"\n@page {{ size: {page_size}; }}\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, suffix=".pdf", delete=False
        ) as handle:
            temporary = Path(handle.name)
        HTML(
            string=build_html(slug, sources),
            base_url=None,
            url_fetcher=lambda *_: (_ for _ in ()).throw(
                ProductionPdfError("external resources are disabled")
            ),
        ).write_pdf(temporary, stylesheets=[CSS(string=css)])
        temporary.replace(output)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return RenderResult(
        selector,
        slug,
        [str(path.relative_to(REPO_ROOT)) for path in sources],
        str(output),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--page-size", choices=("letter", "a4"), default="letter")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--metadata-json", type=Path, help=argparse.SUPPRESS)
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
        print(f"Requested video script: {result.requested_selector}")
        print(f"Resolved video script: {result.resolved_slug}")
        print("Included sources:\n" + "\n".join(result.included_sources))
        print(f"Wrote {result.output_path}")
        if args.metadata_json:
            args.metadata_json.write_text(
                json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8"
            )
    except (OSError, ProductionPdfError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
