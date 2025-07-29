"""Lightweight GitHub API helper."""

from __future__ import annotations

from typing import Any, Dict, List

from .github_auth import get_github_token

import requests

GRAPHQL_URL = "https://api.github.com/graphql"
SEARCH_URL = "https://api.github.com/search/commits"


def fetch_contributions(login: str, start: str, end: str) -> List[Dict[str, Any]]:
    """Return commits authored by *login* in the given date range."""
    token = get_github_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.cloak-preview+json",
    }
    q = f"author:{login}+committer-date:{start}..{end}"
    page = 1
    contributions: List[Dict[str, Any]] = []
    while True:
        url = f"{SEARCH_URL}?q={q}&per_page=100&page={page}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code >= 400:
            raise RuntimeError(f"GitHub API error: {resp.text}")
        data = resp.json()
        for item in data.get("items", []):
            repo = item["repository"]["full_name"]
            contributions.append(
                {
                    "repo": repo,
                    "occurredAt": item["commit"]["author"]["date"],
                    "sha": item["sha"],
                    "url": item["html_url"],
                }
            )
        if "next" not in resp.links:
            break
        page += 1
    return contributions
