"""CLI wrapper for :mod:`generate_contrib_heatmap`."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

try:
    from . import generate_contrib_heatmap as base
except ImportError:  # pragma: no cover - package not installed
    import generate_contrib_heatmap as base  # type: ignore


def main(argv: list[str] | None = None) -> None:
    """Generate the pull-request heatmap SVG."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=base.OUTPUT_PATH)
    args = parser.parse_args(argv)

    year = dt.date.today().year
    dates = base.fetch_pr_dates(year)
    base.generate_heatmap(dates, year, args.out)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
