"""GitHub REST helper for commit stats with simple JSON cache."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import requests

try:
    from .github_auth import get_github_token
except ImportError:  # pragma: no cover - allow module execution without package context
    from github_auth import get_github_token  # pragma: no cover

CACHE_FILE = Path("assets/heatmap_data.json")


def _load_cache() -> Dict[str, Any]:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache))


def fetch_commit_stats(owner: str, repo: str, sha: str) -> Dict[str, int]:
    """Return additions + deletions for commit and cache the result."""
    cache = _load_cache()
    key = f"{owner}/{repo}@{sha}"
    if key in cache:
        return cache[key]

    token = get_github_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    stats = {
        "additions": data.get("stats", {}).get("additions", 0),
        "deletions": data.get("stats", {}).get("deletions", 0),
    }
    cache[key] = stats
    _save_cache(cache)
    return stats
