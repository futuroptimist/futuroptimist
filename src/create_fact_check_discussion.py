"""Create GitHub Discussions for video fact-checks."""

from __future__ import annotations

import argparse
import json
import pathlib
import textwrap
import urllib.request
from typing import Any

from src import github_auth

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
USER_AGENT = "futuroptimist-fact-check-discussions"
REPO_DEFAULT = "futuroptimist/futuroptimist"
CATEGORY_DEFAULT = "Fact Checks"
SCRIPT_NAME = "script.md"
METADATA_NAME = "metadata.json"

_REPOSITORY_QUERY = textwrap.dedent(
    """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 50) {
          nodes { id name }
        }
      }
    }
    """
).strip()

_CREATE_DISCUSSION_MUTATION = textwrap.dedent(
    """
    mutation(
      $repositoryId: ID!
      $categoryId: ID!
      $title: String!
      $body: String!
    ) {
      createDiscussion(
        input: {
          repositoryId: $repositoryId
          categoryId: $categoryId
          title: $title
          body: $body
        }
      ) {
        discussion { url }
      }
    }
    """
).strip()


def _post_graphql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(
        request
    ) as response:  # pragma: no cover - stubbed in tests
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    errors = data.get("errors")
    if errors:
        first = errors[0]
        message = first.get("message", "Unknown GraphQL error")
        raise RuntimeError(f"GitHub GraphQL error: {message}")
    return data.get("data", {})


def _split_repo(repo: str) -> tuple[str, str]:
    if "/" not in repo:
        raise ValueError(f"Repository must be in 'owner/name' format: {repo!r}")
    owner, name = repo.split("/", 1)
    owner = owner.strip()
    name = name.strip()
    if not owner or not name:
        raise ValueError(f"Repository must be in 'owner/name' format: {repo!r}")
    return owner, name


def _fetch_repository(repo: str, token: str) -> tuple[str, dict[str, str]]:
    owner, name = _split_repo(repo)
    data = _post_graphql(
        _REPOSITORY_QUERY,
        {"owner": owner, "name": name},
        token,
    )
    repository = data.get("repository") or {}
    repo_id = repository.get("id")
    if not repo_id:
        raise RuntimeError(f"Repository {repo!r} not found")
    categories: dict[str, str] = {}
    nodes = (repository.get("discussionCategories") or {}).get("nodes") or []
    for node in nodes:
        name_value = node.get("name")
        category_id = node.get("id")
        if isinstance(name_value, str) and isinstance(category_id, str):
            categories[name_value] = category_id
    return repo_id, categories


def load_metadata(video_root: pathlib.Path, slug: str) -> dict[str, Any]:
    meta_path = video_root / slug / METADATA_NAME
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json not found for slug {slug}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def build_title(slug: str, metadata: dict[str, Any]) -> str:
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return f"Fact check: {title.strip()}"
    return f"Fact check: {slug}"


def _youtube_url(metadata: dict[str, Any]) -> str | None:
    youtube_id = metadata.get("youtube_id")
    if isinstance(youtube_id, str) and youtube_id.strip():
        return f"https://www.youtube.com/watch?v={youtube_id.strip()}"
    return None


def build_body(slug: str, metadata: dict[str, Any]) -> str:
    script_path = f"video_scripts/{slug}/{SCRIPT_NAME}"
    youtube = _youtube_url(metadata)
    description = metadata.get("description")
    title_value = metadata.get("title")
    if isinstance(title_value, str) and title_value.strip():
        display_title = title_value.strip()
    else:
        display_title = slug
    lines = [
        f"Help fact-check **{display_title}** before it goes live.",
        "",
        "## Context",
        f"- Script draft: `{script_path}`",
    ]
    if youtube:
        lines.append(f"- Reference cut: {youtube}")
    publish_date = metadata.get("publish_date")
    if isinstance(publish_date, str) and publish_date.strip():
        lines.append(f"- Target publish date: {publish_date.strip()}")
    summary = metadata.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.extend(["", summary.strip()])
    elif isinstance(description, str) and description.strip():
        lines.extend(["", description.strip()])
    lines.extend(
        [
            "",
            "## What to look for",
            "- Flag factual inaccuracies, missing citations, or ambiguous claims.",
            "- Drop timestamp suggestions or source links as replies.",
            "- Note visuals or data that should be double-checked before publish.",
            "",
            "## How to contribute",
            "1. Quote the line you're checking.",
            "2. Provide a source or correction.",
            "3. Mark resolved items with a reaction so others know it's handled.",
        ]
    )
    return "\n".join(lines) + "\n"


def create_discussion(
    *, repo: str, category_name: str, title: str, body: str, token: str
) -> str:
    repository_id, categories = _fetch_repository(repo, token)
    category_id = categories.get(category_name)
    if not category_id:
        available = ", ".join(sorted(categories)) or "no categories"
        raise RuntimeError(
            f"Discussion category {category_name!r} not found. Available: {available}"
        )
    data = _post_graphql(
        _CREATE_DISCUSSION_MUTATION,
        {
            "repositoryId": repository_id,
            "categoryId": category_id,
            "title": title,
            "body": body,
        },
        token,
    )
    url = ((data.get("createDiscussion") or {}).get("discussion") or {}).get("url")
    if not url:
        raise RuntimeError("GitHub did not return a discussion URL")
    return url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a GitHub Discussion for fact-checking a video script",
    )
    parser.add_argument("slug", help="Video slug like 20240101_example-video")
    parser.add_argument(
        "--video-root",
        default=pathlib.Path("video_scripts"),
        type=pathlib.Path,
        help="Directory containing video script folders",
    )
    parser.add_argument(
        "--repo",
        default=REPO_DEFAULT,
        help="Repository owner/name to create the discussion in",
    )
    parser.add_argument(
        "--category",
        default=CATEGORY_DEFAULT,
        help="Discussion category name",
    )
    args = parser.parse_args(argv)

    video_root = pathlib.Path(args.video_root).resolve()
    metadata = load_metadata(video_root, args.slug)
    token = github_auth.get_github_token()
    title = build_title(args.slug, metadata)
    body = build_body(args.slug, metadata)
    url = create_discussion(
        repo=args.repo,
        category_name=args.category,
        title=title,
        body=body,
        token=token,
    )
    print(f"Created discussion: {url}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
