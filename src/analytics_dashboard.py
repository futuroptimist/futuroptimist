"""Streamlit dashboard for Futuroptimist YouTube analytics.

The Futuroptimist roadmap (see Phase 5 in ``INSTRUCTIONS.md``) promises a
dashboard that visualises topic performance alongside retention metrics.  This
module fulfils that commitment by loading the analytics captured in
``video_scripts/*/metadata.json`` (populated via ``analytics_ingester.py``) and
exposing a small Streamlit interface.  The helpers are structured so they can
be unit-tested without launching Streamlit, keeping CI deterministic.
"""

from __future__ import annotations

import json
import pathlib
from typing import Iterable

import pandas as pd


VIDEO_ROOT = pathlib.Path("video_scripts")
ANALYTICS_FIELDS = [
    "views",
    "watch_time_minutes",
    "average_view_duration_seconds",
    "impressions",
    "impressions_click_through_rate",
]


def load_video_metadata(video_root: pathlib.Path = VIDEO_ROOT) -> list[dict]:
    """Return flattened analytics records from ``video_root``.

    Each record contains the script slug, core metadata fields, and analytics
    metrics captured by :mod:`src.analytics_ingester`.
    """

    video_root = video_root.resolve()
    records: list[dict] = []
    for meta_path in sorted(video_root.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        analytics = data.get("analytics") or {}
        record = {
            "slug": meta_path.parent.name,
            "title": str(data.get("title", "")),
            "status": str(data.get("status", "")),
            "publish_date": str(data.get("publish_date", "")),
            "view_count": _as_int(data.get("view_count")),
        }
        for field in ANALYTICS_FIELDS:
            record[field] = analytics.get(field)
        records.append(record)
    return records


def build_dataframe(records: Iterable[dict]) -> pd.DataFrame:
    """Return a Pandas dataframe sorted by publish date."""

    frame = pd.DataFrame(records)
    required_columns = [
        "slug",
        "title",
        "status",
        "publish_date",
        "view_count",
        *ANALYTICS_FIELDS,
    ]

    if frame.empty:
        return pd.DataFrame(columns=required_columns)

    for column in required_columns:
        if column not in frame.columns:
            frame[column] = pd.NA

    if "publish_date" in frame.columns:
        frame["publish_date"] = pd.to_datetime(frame["publish_date"], errors="coerce")
    numeric_columns = {"view_count", *ANALYTICS_FIELDS}
    for column in numeric_columns & set(frame.columns):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame.sort_values(["publish_date", "slug"], inplace=True, ignore_index=True)
    return frame


def summarize_dataframe(frame: pd.DataFrame) -> dict[str, float | int]:
    """Return aggregate metrics for dashboard headline numbers."""

    if frame.empty:
        return {
            "videos": 0,
            "total_views": 0,
            "total_watch_time_minutes": 0.0,
            "average_view_duration_seconds": 0.0,
            "average_ctr": 0.0,
        }

    views = float(frame.get("views", pd.Series(dtype=float)).sum())
    watch = float(frame.get("watch_time_minutes", pd.Series(dtype=float)).sum())
    average_duration = float(
        frame.get("average_view_duration_seconds", pd.Series(dtype=float)).mean() or 0.0
    )
    average_ctr_fraction = float(
        frame.get("impressions_click_through_rate", pd.Series(dtype=float)).mean()
        or 0.0
    )
    average_ctr = average_ctr_fraction * 100
    return {
        "videos": int(len(frame)),
        "total_views": int(round(views)),
        "total_watch_time_minutes": round(watch, 2),
        "average_view_duration_seconds": round(average_duration, 2),
        "average_ctr": round(average_ctr, 2),
    }


def render_dashboard(video_root: pathlib.Path = VIDEO_ROOT) -> None:
    """Render the Streamlit dashboard for analytics exploration."""

    import streamlit as st

    st.set_page_config(page_title="Futuroptimist Analytics", layout="wide")
    st.title("Futuroptimist Analytics Dashboard")
    st.caption("Visualise YouTube retention metrics captured by analytics_ingester.py")

    records = load_video_metadata(video_root)
    statuses = sorted({r["status"] for r in records if r.get("status")})
    options = ["All"] + statuses if statuses else ["All"]
    selected_status = st.sidebar.selectbox("Video status", options, index=0)

    if selected_status != "All":
        records = [r for r in records if r.get("status") == selected_status]

    frame = build_dataframe(records)
    summary = summarize_dataframe(frame)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Videos", summary["videos"])
    metric_cols[1].metric("Total views", f"{summary['total_views']:,}")
    metric_cols[2].metric(
        "Total watch time (minutes)", f"{summary['total_watch_time_minutes']:,}"
    )
    metric_cols[3].metric(
        "Average view duration (s)", f"{summary['average_view_duration_seconds']:.1f}"
    )
    metric_cols[4].metric("Average CTR (%)", f"{summary['average_ctr']:.2f}")

    display_frame = frame.copy()
    if not display_frame.empty:
        display_frame["publish_date"] = display_frame["publish_date"].dt.date
        if "impressions_click_through_rate" in display_frame.columns:
            display_frame.loc[:, "impressions_click_through_rate"] = (
                display_frame["impressions_click_through_rate"] * 100
            )
    st.dataframe(
        display_frame[
            [
                "publish_date",
                "title",
                "views",
                "watch_time_minutes",
                "average_view_duration_seconds",
                "impressions",
                "impressions_click_through_rate",
            ]
        ],
        use_container_width=True,
    )

    if not frame.empty and "publish_date" in frame:
        chart_data = frame.dropna(subset=["publish_date"]).set_index("publish_date")
        if not chart_data.empty:
            st.subheader("Performance over time")
            st.line_chart(chart_data[["views", "impressions"]])

            if (
                "watch_time_minutes" in chart_data.columns
                and not chart_data["watch_time_minutes"].dropna().empty
            ):
                st.subheader("Watch time (minutes)")
                st.line_chart(chart_data[["watch_time_minutes"]])

            if (
                "impressions_click_through_rate" in chart_data.columns
                and not chart_data["impressions_click_through_rate"].dropna().empty
            ):
                st.subheader("Click-through rate (%)")
                ctr_chart = chart_data[["impressions_click_through_rate"]].mul(100)
                st.line_chart(ctr_chart)

            if (
                "average_view_duration_seconds" in chart_data.columns
                and not chart_data["average_view_duration_seconds"].dropna().empty
            ):
                st.subheader("Average view duration")
                st.bar_chart(chart_data[["average_view_duration_seconds"]])


def _as_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main() -> None:  # pragma: no cover - exercised via Streamlit runtime
    render_dashboard()


if __name__ == "__main__":  # pragma: no cover
    main()
