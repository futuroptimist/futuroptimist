"""CLI wrapper for :mod:`generate_annual_contributions`."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from . import generate_annual_contributions as base
except ImportError:  # pragma: no cover - package not installed
    import generate_annual_contributions as base  # type: ignore


def main(argv: list[str] | None = None) -> None:
    """Generate yearly PR charts."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=base.SVG_OUTPUT)
    args = parser.parse_args(argv)

    counts = base.fetch_counts()
    base.generate_chart(counts, args.out)
    base.write_csv(counts)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
