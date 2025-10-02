#!/usr/bin/env python3
"""Generate docs/prompt-docs-summary.md from prompt docs."""
import argparse
import pathlib
import urllib.request
import urllib.parse

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


def _fetch_codex_context(url: str) -> tuple[str, str, str, str, str, str, str, str]:
    parsed = urllib.parse.urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "blob":
        raise ValueError(f"unsupported prompts-codex URL: {url}")
    owner, repo, _, ref, *rest = parts
    codex_path = "/".join(rest)
    base_dir = "/".join(rest[:-1])
    raw_codex = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{codex_path}"
    with urllib.request.urlopen(
        raw_codex
    ) as resp:  # pragma: no cover - network stubbed
        text = resp.read().decode("utf-8")

    root_raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/"
    root_html = f"https://github.com/{owner}/{repo}/blob/{ref}/"
    dir_raw = root_raw + (base_dir + "/" if base_dir else "")
    dir_html = root_html + (base_dir + "/" if base_dir else "")
    return text, repo, codex_path, root_raw, root_html, dir_raw, dir_html, url


def _build_related_rows(
    text: str,
    repo: str,
    root_raw: str,
    root_html: str,
    dir_raw: str,
    dir_html: str,
) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for rel in extract_related_links(text):
        anchor = ""
        if "#" in rel:
            rel, anchor = rel.split("#", 1)
            anchor = f"#{anchor}"
        rel_path = rel.lstrip("/")
        if not rel_path.endswith(".md"):
            rel_path = f"{rel_path}.md"
        if rel.startswith("/"):
            raw = root_raw + rel_path
            html = root_html + rel_path + anchor
        else:
            raw = dir_raw + rel_path
            html = dir_html + rel_path + anchor
        with urllib.request.urlopen(raw) as doc:  # pragma: no cover - network stubbed
            title = (
                parse_title_lines(doc.read().decode("utf-8").splitlines()) or rel_path
            )
        display = f"{repo}/{rel_path}{anchor}"
        rows.append((display, html, title))
    return rows


def fetch_remote_titles(url: str) -> list[tuple[str, str, str]]:
    """Fetch remote prompt docs referenced by a prompts-codex URL."""

    text, repo, _codex_path, root_raw, root_html, dir_raw, dir_html, _ = (
        _fetch_codex_context(url)
    )
    return _build_related_rows(text, repo, root_raw, root_html, dir_raw, dir_html)


def fetch_repo_prompt_rows(url: str) -> list[tuple[str, str, str]]:
    """Return rows for a prompts doc and the guides it links to."""

    text, repo, codex_path, root_raw, root_html, dir_raw, dir_html, html_url = (
        _fetch_codex_context(url)
    )
    title = parse_title_lines(text.splitlines()) or codex_path
    rows = [(f"{repo}/{codex_path}", html_url, title)]
    rows.extend(_build_related_rows(text, repo, root_raw, root_html, dir_raw, dir_html))
    return rows


def _parse_repo_list(path: pathlib.Path) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        ref = "main"
        if "@" in line:
            line, ref = line.split("@", 1)
            ref = ref.strip() or "main"
        if "/" in line:
            owner, repo = line.split("/", 1)
        else:
            owner, repo = "futuroptimist", line
        owner = owner.strip()
        repo = repo.strip()
        if not owner or not repo:
            continue
        entries.append((owner, repo, ref))
    return entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos-from", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument(
        "--external-prompts-codex",
        type=str,
        action="append",
        default=[],
    )
    args = parser.parse_args()

    # Ensure repos-from exists even if unused.
    if not args.repos_from.exists():
        raise FileNotFoundError(args.repos_from)

    docs_dir = pathlib.Path("docs")
    rows: list[tuple[str, str, str]] = []
    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir).as_posix()
        if path.resolve() == args.out.resolve() or "prompts" not in rel:
            continue
        title = parse_title(path)
        rows.append((rel, rel, title))

    remote_rows: list[tuple[str, str, str]] = []
    for owner, repo, ref in _parse_repo_list(args.repos_from):
        codex_url = f"https://github.com/{owner}/{repo}/blob/{ref}/docs/prompts/codex/automation.md"
        try:
            remote_rows.extend(fetch_repo_prompt_rows(codex_url))
        except Exception:
            continue

    for codex in args.external_prompts_codex:
        try:
            remote_rows.extend(fetch_repo_prompt_rows(codex))
        except Exception:
            continue

    remote_rows.sort(key=lambda r: r[0])
    rows.extend(remote_rows)

    lines = [
        "# Prompt Docs Summary",
        "",
        "| Path | Description |",
        "|------|-------------|",
    ]
    seen: set[str] = set()
    for display, link, title in rows:
        if display in seen:
            continue
        seen.add(display)
        lines.append(f"| [{display}]({link}) | {title} |")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
