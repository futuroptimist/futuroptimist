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
    query($login:String!, $from:DateTime!, $to:DateTime!, $cursor:String) {
      user(login:$login) {
        contributionsCollection(from:$from, to:$to) {
          commitContributionsByRepository(first:100 after:$cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
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
    }
    """
    contributions: List[Dict[str, Any]] = []
    cursor = None
    while True:
        variables = {
            "login": login,
            "from": start,
            "to": end,
            "cursor": cursor,
        }
        resp = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        coll = data["data"]["user"]["contributionsCollection"][
            "commitContributionsByRepository"
        ]
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
        if not coll["pageInfo"]["hasNextPage"]:
            break
        cursor = coll["pageInfo"]["endCursor"]
    return contributions
