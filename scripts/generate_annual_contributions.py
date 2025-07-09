"""Generate a bar chart of yearly pull request counts."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import sys

import matplotlib.pyplot as plt

try:  # allow package or standalone execution
    from .generate_contrib_heatmap import fetch_pr_dates
except ImportError:  # pragma: no cover - direct script execution
    sys.path.append(str(Path(__file__).resolve().parent))
    from generate_contrib_heatmap import fetch_pr_dates  # type: ignore

OUTPUT_PATH = Path("assets/annual_contribs.svg")


def fetch_counts(start_year: int = 2021, end_year: int | None = None) -> dict[int, int]:
    """Return yearly PR counts from ``start_year`` to ``end_year`` inclusive."""
    end_year = end_year or dt.date.today().year
    counts: dict[int, int] = {}
    for year in range(start_year, end_year + 1):
        counts[year] = len(fetch_pr_dates(year))
    return counts


def generate_chart(counts: dict[int, int], output: Path = OUTPUT_PATH) -> None:
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


def main() -> None:
    counts = fetch_counts()
    generate_chart(counts)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
