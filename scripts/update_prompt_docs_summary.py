#!/usr/bin/env python3
"""Generate docs/prompt-docs-summary.md from prompt docs."""
import argparse
import pathlib
import urllib.request

import yaml


def parse_title_lines(lines: list[str]) -> str:
    """Return the title from Markdown lines."""

    if lines and lines[0].strip() == "---":
        try:
            end = lines[1:].index("---") + 1
            front = "\n".join(lines[1:end])
            data = yaml.safe_load(front) or {}
            if "title" in data:
                return str(data["title"])
            lines = lines[end + 1 :]
        except ValueError:
            lines = lines[1:]
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def parse_title(path: pathlib.Path) -> str:
    return parse_title_lines(path.read_text(encoding="utf-8").splitlines()) or path.stem


def extract_related_links(text: str) -> list[str]:
    """Return relative links from the 'Related prompt guides' section."""

    lines = text.splitlines()
    try:
        start = lines.index("## Related prompt guides") + 1
    except ValueError:
        return []
    links = []
    for line in lines[start:]:
        if line.strip().startswith("## "):
            break
        if line.strip().startswith("-") and "(" in line and ")" in line:
            link = line.split("(", 1)[1].split(")", 1)[0]
            links.append(link)
    return links


def fetch_remote_titles(url: str) -> list[tuple[str, str, str]]:
    """Fetch remote prompt docs referenced by a prompts-codex URL."""

    with urllib.request.urlopen(
        url
    ) as resp:  # pragma: no cover - network stubbed in tests
        text = resp.read().decode("utf-8")
    rows = []
    for rel in extract_related_links(text):
        anchor = ""
        if "#" in rel:
            rel, anchor = rel.split("#", 1)
            anchor = f"#{anchor}"
        if rel.startswith("/docs/"):
            rel_path = rel[len("/docs/") :]
        else:
            rel_path = rel.lstrip("/")
        filename = f"{rel_path}.md"
        raw = (
            "https://raw.githubusercontent.com/democratizedspace/dspace/v3/frontend/src/pages/docs/md/"
            f"{filename}"
        )
        with urllib.request.urlopen(
            raw
        ) as doc:  # pragma: no cover - network stubbed in tests
            title = (
                parse_title_lines(doc.read().decode("utf-8").splitlines()) or filename
            )
        html = (
            "https://github.com/democratizedspace/dspace/blob/v3/frontend/src/pages/docs/md/"
            f"{filename}{anchor}"
        )
        display = f"dspace/{filename}"
        rows.append((display, html, title))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos-from", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--external-prompts-codex", type=str, default=None)
    args = parser.parse_args()

    # Ensure repos-from exists even if unused.
    if not args.repos_from.exists():
        raise FileNotFoundError(args.repos_from)

    docs_dir = pathlib.Path("docs")
    rows = []
    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir).as_posix()
        if path.resolve() == args.out.resolve() or "prompts" not in rel:
            continue
        title = parse_title(path)
        rows.append((rel, rel, title))

    if args.external_prompts_codex:
        rows.extend(fetch_remote_titles(args.external_prompts_codex))

    lines = [
        "# Prompt Docs Summary",
        "",
        "| Path | Description |",
        "|------|-------------|",
    ]
    for display, link, title in rows:
        lines.append(f"| [{display}]({link}) | {title} |")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
