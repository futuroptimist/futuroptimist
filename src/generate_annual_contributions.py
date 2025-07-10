"""Generate yearly contribution stats and chart."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
import sys
import os
import collections
import requests
import urllib.parse

import csv

import matplotlib.pyplot as plt

_GH = "https://api.github.com/search/issues"
_HDR = {"Accept": "application/vnd.github+json"}
if tok := os.getenv("GITHUB_TOKEN"):
    _HDR["Authorization"] = f"Bearer {tok}"

SVG_OUTPUT = Path("assets/annual_contribs.svg")
CSV_OUTPUT = Path("assets/annual_contribs.csv")


def _search_total(q: str, request_fn=requests.get) -> int:
    """Return GitHub Search API ``total_count`` for *q*."""
    url = f"{_GH}?q={urllib.parse.quote_plus(q)}&per_page=1"
    resp = request_fn(url, headers=_HDR, timeout=30)
    resp.raise_for_status()
    return resp.json()["total_count"]


def fetch_counts(
    user: str | None = None,
    start_year: int = 2021,
    request_fn=requests.get,
) -> collections.OrderedDict[int, int]:
    """Return yearly merged PR counts authored by ``user`` in their repos."""
    user = user or os.getenv("GITHUB_USER") or os.getenv("GITHUB_USERNAME")
    if not user:
        raise RuntimeError("Set GITHUB_USER or pass `user=` explicitly.")

    now = _dt.datetime.utcnow().year
    counts: dict[int, int] = {}
    for yr in range(start_year, now + 1):
        q = (
            f"author:{user} user:{user} is:pr is:merged "
            f"created:{yr}-01-01..{yr}-12-31"
        )
        n = _search_total(q, request_fn)
        if n == 1000:
            print(
                f"[warn] {yr} hit Search API cap (1000). Counts may be truncated.",
                file=sys.stderr,
            )
        counts[yr] = n

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
    ax.set_ylabel("PRs")
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
