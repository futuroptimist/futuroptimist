"""Lightweight GitHub GraphQL helper."""

from __future__ import annotations

import os
import requests
from typing import Any, Dict, List

API_URL = "https://api.github.com/graphql"


def fetch_contributions(login: str, start: str, end: str) -> List[Dict[str, Any]]:
    """Return commits authored by *login* in the given date range."""
    token = os.environ["GH_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    query = """
    query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) {
        contributionsCollection(from:$from, to:$to) {
          commitContributionsByRepository(maxRepositories:100) {
            repository { nameWithOwner }
            contributions(first:100) {
              nodes {
                occurredAt
                commit { oid url }
              }
            }
          }
        }
      }
    }
    """
    variables = {"login": login, "from": start, "to": end}
    resp = requests.post(
        API_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GitHub GraphQL errors: {data['errors']}")
    if "data" not in data or not data["data"].get("user"):
        raise RuntimeError(f"Unexpected GraphQL response: {data}")
    coll = data["data"]["user"]["contributionsCollection"][
        "commitContributionsByRepository"
    ]
    contributions: List[Dict[str, Any]] = []
    for node in coll.get("nodes", []):
        repo = node["repository"]["nameWithOwner"]
        for c in node["contributions"]["nodes"]:
            contributions.append(
                {
                    "repo": repo,
                    "occurredAt": c["occurredAt"],
                    "sha": c["commit"]["oid"],
                    "url": c["commit"]["url"],
                }
            )
    return contributions
