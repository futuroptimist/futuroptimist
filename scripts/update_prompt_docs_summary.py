#!/usr/bin/env python3
"""Generate docs/prompt-docs-summary.md from prompt docs."""
import argparse
import pathlib
import yaml


def parse_title(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8").splitlines()
    if text and text[0].strip() == "---":
        try:
            end = text[1:].index("---") + 1
            front = "\n".join(text[1:end])
            data = yaml.safe_load(front) or {}
            if "title" in data:
                return str(data["title"])
            text = text[end + 1 :]
        except ValueError:
            text = text[1:]
    for line in text:
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos-from", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    # Ensure repos-from exists even if unused.
    if not args.repos_from.exists():
        raise FileNotFoundError(args.repos_from)

    docs_dir = pathlib.Path("docs")
    rows = []
    for path in sorted(docs_dir.rglob("*.md")):
        if path.resolve() == args.out.resolve():
            continue
        rel = path.relative_to(docs_dir).as_posix()
        title = parse_title(path)
        rows.append((rel, title))

    lines = [
        "# Prompt Docs Summary",
        "",
        "| Path | Description |",
        "|------|-------------|",
    ]
    for rel, title in rows:
        lines.append(f"| [{rel}]({rel}) | {title} |")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
