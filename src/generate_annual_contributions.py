"""Generate yearly contribution stats and chart.

Counts issues, pull requests and commits authored across all repositories so
totals more closely mirror the public GitHub profile contributions graph.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
import sys
import os
import csv
import collections
import urllib.parse
import requests

import matplotlib.pyplot as plt

SVG_OUTPUT = Path("assets/annual_contribs.svg")
CSV_OUTPUT = Path("assets/annual_contribs.csv")

_GH = "https://api.github.com/search/issues"
_HDR = {"Accept": "application/vnd.github+json"}
_COMMITS = "https://api.github.com/search/commits"
_HDR_COMMITS = {"Accept": "application/vnd.github.cloak-preview+json"}
if tok := os.getenv("GITHUB_TOKEN"):
    _HDR["Authorization"] = f"Bearer {tok}"
    _HDR_COMMITS["Authorization"] = f"Bearer {tok}"


def _search_total(
    q: str,
    request_fn: callable = requests.get,
    headers: dict[str, str] | None = None,
) -> int:
    """Return GitHub Search API ``total_count`` for *q*."""
    url = f"{_GH}?q={urllib.parse.quote_plus(q)}&per_page=1"
    resp = request_fn(url, headers=headers or _HDR, timeout=30)
    resp.raise_for_status()
    return resp.json()["total_count"]


def _search_commit_total(q: str, request_fn=requests.get) -> int:
    """Return commit search ``total_count`` for *q*."""
    url = f"{_COMMITS}?q={urllib.parse.quote_plus(q)}&per_page=1"
    resp = request_fn(url, headers=_HDR_COMMITS, timeout=30)
    resp.raise_for_status()
    return resp.json()["total_count"]


def fetch_counts(
    user: str | None = None,
    start_year: int = 2021,
    request_fn=requests.get,
) -> "collections.OrderedDict[int, int]":
    """Return ``{year: contributions}`` authored by *user*.

    Contributions include issues, pull requests, and commits created by the user
    across all repositories. This approximates GitHub's public contributions
    graph.
    """

    user = user or os.getenv("GITHUB_USER") or os.getenv("GITHUB_USERNAME")
    if not user:
        raise RuntimeError("Set GITHUB_USER or pass `user=` explicitly.")

    now = _dt.datetime.utcnow().year
    counts: dict[int, int] = {}
    for year in range(start_year, now + 1):
        q_pr = f"author:{user} is:pr created:{year}-01-01..{year}-12-31"
        pr_n = _search_total(q_pr, request_fn)
        if pr_n == 1000:
            print(
                f"[warn] PR query for {year} hit Search API cap (1000).",
                file=sys.stderr,
            )

        q_issue = f"author:{user} is:issue created:{year}-01-01..{year}-12-31"
        issue_n = _search_total(q_issue, request_fn)
        if issue_n == 1000:
            print(
                f"[warn] Issue query for {year} hit Search API cap (1000).",
                file=sys.stderr,
            )

        q_commit = f"author:{user} committer-date:{year}-01-01..{year}-12-31"
        commit_n = _search_total(q_commit, request_fn, headers=_HDR_COMMITS)
        if commit_n == 1000:
            print(
                f"[warn] Commit query for {year} hit Search API cap (1000).",
                file=sys.stderr,
            )

        counts[year] = pr_n + issue_n + commit_n

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
