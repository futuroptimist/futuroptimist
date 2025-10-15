import json
import sys
from pathlib import Path

import pandas as pd
import pytest

import src.analytics_dashboard as dashboard


def _write_metadata(root: Path, slug: str, payload: dict) -> Path:
    meta_path = root / slug / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text(json.dumps(payload))
    return meta_path


def test_load_video_metadata_includes_analytics(tmp_path: Path) -> None:
    video_root = tmp_path / "video_scripts"
    video_root.mkdir()
    payload = {
        "youtube_id": "abc123",
        "title": "Orbital Hydroponics",
        "status": "live",
        "publish_date": "2025-01-15",
        "view_count": 42000,
        "analytics": {
            "views": 41000,
            "watch_time_minutes": 1350.5,
            "average_view_duration_seconds": 240.2,
            "impressions": 120000,
            "impressions_click_through_rate": 0.042,
        },
    }
    _write_metadata(video_root, "20250115_orbital-hydroponics", payload)

    records = dashboard.load_video_metadata(video_root)

    assert len(records) == 1
    record = records[0]
    assert record["slug"] == "20250115_orbital-hydroponics"
    assert record["title"] == "Orbital Hydroponics"
    assert record["status"] == "live"
    assert record["publish_date"] == "2025-01-15"
    assert record["view_count"] == 42000
    assert record["views"] == 41000
    assert record["watch_time_minutes"] == 1350.5
    assert record["average_view_duration_seconds"] == 240.2
    assert record["impressions"] == 120000
    assert record["impressions_click_through_rate"] == 0.042


def test_build_dataframe_sorts_and_casts() -> None:
    records = [
        {
            "slug": "20250102_second-video",
            "title": "Second",
            "status": "live",
            "publish_date": "2025-01-02",
            "view_count": 200,
            "views": 180,
            "watch_time_minutes": 50.0,
            "average_view_duration_seconds": 220.0,
            "impressions": 900,
            "impressions_click_through_rate": 0.05,
        },
        {
            "slug": "20250101_first-video",
            "title": "First",
            "status": "live",
            "publish_date": "2025-01-01",
            "view_count": 100,
            "views": 90,
            "watch_time_minutes": 25.0,
            "average_view_duration_seconds": 180.0,
            "impressions": 500,
            "impressions_click_through_rate": 0.04,
        },
    ]

    df = dashboard.build_dataframe(records)

    assert list(df["slug"]) == ["20250101_first-video", "20250102_second-video"]
    assert pd.api.types.is_datetime64_any_dtype(df["publish_date"])
    assert pd.api.types.is_numeric_dtype(df["views"])
    assert pd.api.types.is_numeric_dtype(df["watch_time_minutes"])


def test_summarize_dataframe_handles_metrics() -> None:
    records = [
        {
            "slug": "a",
            "title": "A",
            "status": "live",
            "publish_date": "2025-01-01",
            "views": 100,
            "watch_time_minutes": 40.0,
            "average_view_duration_seconds": 200.0,
            "impressions": 1000,
            "impressions_click_through_rate": 0.05,
        },
        {
            "slug": "b",
            "title": "B",
            "status": "live",
            "publish_date": "2025-01-02",
            "views": 300,
            "watch_time_minutes": 60.0,
            "average_view_duration_seconds": 260.0,
            "impressions": 2000,
            "impressions_click_through_rate": 0.06,
        },
    ]
    df = dashboard.build_dataframe(records)

    summary = dashboard.summarize_dataframe(df)

    assert summary["videos"] == 2
    assert summary["total_views"] == 400
    assert summary["total_watch_time_minutes"] == 100.0
    assert summary["average_view_duration_seconds"] == pytest.approx(230.0)
    assert summary["average_ctr"] == pytest.approx(5.5)


def test_summarize_dataframe_empty() -> None:
    empty_df = dashboard.build_dataframe([])

    summary = dashboard.summarize_dataframe(empty_df)

    assert summary == {
        "videos": 0,
        "total_views": 0,
        "total_watch_time_minutes": 0.0,
        "average_view_duration_seconds": 0.0,
        "average_ctr": 0.0,
    }


def test_render_dashboard_displays_watch_time_and_ctr_charts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    video_root = tmp_path / "video_scripts"
    video_root.mkdir()
    payload = {
        "youtube_id": "chart123",
        "title": "Chart Feature",
        "status": "live",
        "publish_date": "2025-02-01",
        "view_count": 1234,
        "analytics": {
            "views": 1200,
            "watch_time_minutes": 345.6,
            "average_view_duration_seconds": 210.0,
            "impressions": 5678,
            "impressions_click_through_rate": 0.065,
        },
    }
    _write_metadata(video_root, "20250201_chart-feature", payload)

    class DummyStreamlit:
        def __init__(self) -> None:
            self.metrics: list[tuple[str, object]] = []
            self.line_chart_data: list[object] = []
            self.bar_chart_data: list[object] = []
            self.subheaders: list[str] = []
            self.dataframes: list[object] = []
            self.selectboxes: list[tuple[str, list[str], int]] = []
            self.columns_count: int | None = None
            self.sidebar = self.Sidebar(self)

        class Sidebar:
            def __init__(self, parent: "DummyStreamlit") -> None:
                self._parent = parent

            def selectbox(self, label: str, options: list[str], index: int = 0) -> str:
                self._parent.selectboxes.append((label, options, index))
                return options[index]

        class Column:
            def __init__(self, parent: "DummyStreamlit") -> None:
                self._parent = parent

            def metric(self, label: str, value: object, *args, **kwargs) -> None:
                self._parent.metrics.append((label, value))

        @staticmethod
        def _snapshot(data: object) -> object:
            if hasattr(data, "copy"):
                try:
                    return data.copy()  # type: ignore[call-arg]
                except TypeError:
                    return data
            return data

        def set_page_config(self, **_kwargs) -> None:  # pragma: no cover - trivial stub
            return None

        def title(self, _text: str) -> None:  # pragma: no cover - trivial stub
            return None

        def caption(self, _text: str) -> None:  # pragma: no cover - trivial stub
            return None

        def columns(self, count: int) -> list["DummyStreamlit.Column"]:
            self.columns_count = count
            return [self.Column(self) for _ in range(count)]

        def dataframe(self, data, use_container_width: bool = False) -> None:
            self.dataframes.append(self._snapshot(data))

        def line_chart(self, data) -> None:
            self.line_chart_data.append(self._snapshot(data))

        def bar_chart(self, data) -> None:
            self.bar_chart_data.append(self._snapshot(data))

        def subheader(self, text: str) -> None:
            self.subheaders.append(text)

    stub = DummyStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", stub)

    dashboard.render_dashboard(video_root=video_root)

    assert stub.columns_count == 5
    metric_labels = [label for label, _ in stub.metrics]
    assert "Average CTR (%)" in metric_labels
    assert any(
        "watch_time_minutes" in getattr(data, "columns", [])
        for data in stub.line_chart_data
    )
    ctr_chart_frames = [
        data
        for data in stub.line_chart_data
        if "impressions_click_through_rate" in getattr(data, "columns", [])
    ]
    assert ctr_chart_frames
    ctr_metric_value = next(
        value for label, value in stub.metrics if label == "Average CTR (%)"
    )
    assert ctr_metric_value == "6.50"
    ctr_values = ctr_chart_frames[0]["impressions_click_through_rate"].tolist()
    assert all(value == pytest.approx(6.5) for value in ctr_values)
    assert "Watch time (minutes)" in stub.subheaders
    assert "Click-through rate (%)" in stub.subheaders
