"""Generate LOC-weighted 3-D heatmap SVGs."""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from collections import defaultdict

import svgwrite as sw

import sys

try:  # imports succeed when run as package
    from .gh_graphql import fetch_contributions
    from .gh_rest import fetch_commit_stats
    from .svg3d import CELL, draw_bar
except ImportError:  # allow execution as a standalone script
    sys.path.append(str(Path(__file__).resolve().parent))
    from gh_graphql import fetch_contributions
    from gh_rest import fetch_commit_stats
    from svg3d import CELL, draw_bar

MAX_H = 40


def aggregate_loc(contribs):
    loc_by_day = defaultdict(int)
    for c in contribs:
        date = c["occurredAt"][:10]
        owner, repo = c["repo"].split("/")
        stats = fetch_commit_stats(owner, repo, c["sha"])
        loc = stats["additions"] + stats["deletions"]
        loc_by_day[date] += loc
    return loc_by_day


def draw_bars(dwg, loc_by_day, start):
    for i in range(370):
        day = start + dt.timedelta(days=i)
        key = day.isoformat()
        loc = loc_by_day.get(key, 0)
        if loc == 0:
            continue
        week = i // 7
        dow = day.weekday()
        x = 10 + week * CELL
        y = MAX_H + 10 + dow * CELL
        h = 0 if loc == 0 else 4 + (math.log10(loc) / math.log10(1000)) * (MAX_H - 4)
        draw_bar(dwg, x, y, h, "#4c9aff")


def main() -> None:
    today = dt.date.today()
    start = today - dt.timedelta(days=370)
    contribs = fetch_contributions("futuroptimist", str(start), str(today))
    loc_by_day = aggregate_loc(contribs)
    for theme in ("light", "dark"):
        path = Path(f"assets/heatmap_{theme}.svg")
        path.parent.mkdir(parents=True, exist_ok=True)
        dwg = sw.Drawing(path, size=(53 * CELL + 20, 7 * CELL + MAX_H + 20))
        draw_bars(dwg, loc_by_day, start)
        dwg.save()


if __name__ == "__main__":
    main()
