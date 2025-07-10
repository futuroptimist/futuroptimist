"""Generate yearly contribution stats and chart.

Fetches contribution totals via GitHub's GraphQL ``contributionsCollection`` so
the values match the public profile graph. Requires ``GH_TOKEN`` (or
``GITHUB_TOKEN``) with ``repo`` and ``read:org`` scopes if private or
organization work should be included.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
import os
import csv
import collections
import requests

import matplotlib.pyplot as plt

SVG_OUTPUT = Path("assets/annual_contribs.svg")
CSV_OUTPUT = Path("assets/annual_contribs.csv")

API_URL = "https://api.github.com/graphql"

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      totalContributions
    }
  }
}
"""


def fetch_counts(
    user: str | None = None,
    start_year: int = 2021,
    request_fn=requests.post,
) -> "collections.OrderedDict[int, int]":
    """Return ``{year: contributions}`` authored by *user*.

    Uses the GraphQL ``contributionsCollection`` query so totals match what
    GitHub displays on profile pages.
    """

    user = user or os.getenv("GITHUB_USER") or os.getenv("GITHUB_USERNAME")
    if not user:
        raise RuntimeError("Set GITHUB_USER or pass `user=` explicitly.")

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Set GH_TOKEN or GITHUB_TOKEN for authentication.")

    headers = {"Authorization": f"Bearer {token}"}

    now = _dt.datetime.utcnow().year
    counts: dict[int, int] = {}
    for year in range(start_year, now + 1):
        variables = {
            "login": user,
            "from": f"{year}-01-01T00:00:00Z",
            "to": f"{year}-12-31T23:59:59Z",
        }
        resp = request_fn(
            API_URL,
            json={"query": QUERY, "variables": variables},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        count = (
            data.get("data", {})
            .get("user", {})
            .get("contributionsCollection", {})
            .get("totalContributions", 0)
        )
        counts[year] = count

    return collections.OrderedDict(sorted(counts.items()))


def generate_chart(counts: dict[int, int], output: Path = SVG_OUTPUT) -> None:
    """Write an SVG bar chart to ``output`` summarizing ``counts``."""
    years = sorted(counts)
    values = [counts[y] for y in years]

    plt.rcParams.update(
        {
            "text.color": "white",
            "axes.labelcolor": "white",
            "axes.edgecolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "grid.color": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(4, 2))
    ax.bar(years, values, color="#2ecc71")
    ax.set_xticks(years)
    ax.set_ylabel("Contributions")
    ax.grid(axis="y", linewidth=0.25, alpha=0.3)
    for spine in ax.spines.values():
        spine.set_color("white")
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    fig.savefig(output, transparent=True)


def write_csv(counts: dict[int, int], output: Path = CSV_OUTPUT) -> None:
    """Save ``counts`` as ``year,value`` CSV to ``output``."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "count"])
        for year in sorted(counts):
            writer.writerow([year, counts[year]])


def main() -> None:
    counts = fetch_counts()
    generate_chart(counts)
    write_csv(counts)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
