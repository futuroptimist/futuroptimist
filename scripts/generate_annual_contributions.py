"""Generate yearly contribution stats and chart."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import sys

import csv

import matplotlib.pyplot as plt

try:  # allow package or standalone execution
    from .generate_contrib_heatmap import fetch_pr_dates
except ImportError:  # pragma: no cover - direct script execution
    sys.path.append(str(Path(__file__).resolve().parent))
    from generate_contrib_heatmap import fetch_pr_dates  # type: ignore

SVG_OUTPUT = Path("assets/annual_contribs.svg")
CSV_OUTPUT = Path("assets/annual_contribs.csv")


def fetch_counts(start_year: int = 2021, end_year: int | None = None) -> dict[int, int]:
    """Return yearly PR counts from ``start_year`` to ``end_year`` inclusive."""
    end_year = end_year or dt.date.today().year
    counts: dict[int, int] = {}
    for year in range(start_year, end_year + 1):
        counts[year] = len(fetch_pr_dates(year))
    return counts


def generate_chart(counts: dict[int, int], output: Path = SVG_OUTPUT) -> None:
    """Write an SVG bar chart to ``output`` summarizing ``counts``."""
    years = sorted(counts)
    values = [counts[y] for y in years]
    plt.figure(figsize=(4, 2))
    plt.bar(years, values, color="#4c9aff")
    plt.xticks(years)
    plt.ylabel("PRs")
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output, transparent=True)


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
