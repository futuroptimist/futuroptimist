from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src import newsletter_builder


def _write_metadata(
    folder: Path, data: dict, *, script_text: str | None = None
) -> None:
    (folder / "metadata.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    script_body = script_text if script_text is not None else "# Script\n"
    (folder / "script.md").write_text(script_body, encoding="utf-8")


def test_collect_items_orders_and_summarises(tmp_path: Path) -> None:
    video_root = tmp_path / "video_scripts"
    video_root.mkdir()

    alpha = video_root / "20240101_alpha"
    alpha.mkdir()
    _write_metadata(
        alpha,
        {
            "title": "Alpha Launch",
            "publish_date": "2024-01-01",
            "status": "live",
            "summary": "Alpha summary with extra detail that should be trimmed to sentence.",
            "youtube_id": "AAA111",
            "tags": ["rockets", "launch"],
        },
    )

    beta = video_root / "20240201_beta"
    beta.mkdir()
    _write_metadata(
        beta,
        {
            "title": "Beta Update",
            "publish_date": "2024-02-01",
            "status": "live",
            "description": "Beta description first line. Second line should be ignored.",
            "youtube_id": "BBB222",
        },
    )

    gamma = video_root / "20240301_gamma"
    gamma.mkdir()
    _write_metadata(
        gamma,
        {
            "title": "Gamma Sneak Peek",
            "publish_date": "2024-03-01",
            "status": "live",
        },
        script_text=(
            "# Gamma Sneak Peek\n\n"
            "> Video ID: demo\n\n"
            "## Script\n\n"
            "[NARRATOR]: Gamma preview mission hits lab benches this week.\n"
            "[VISUAL]: Lab montage.\n"
        ),
    )

    items = newsletter_builder.collect_items(video_root, statuses={"live"})
    assert [item.slug for item in items] == [
        "20240301_gamma",
        "20240201_beta",
        "20240101_alpha",
    ]

    assert items[0].summary == "Gamma preview mission hits lab benches this week."
    assert "Beta description first line." in items[1].summary
    assert "Alpha summary with extra detail" in items[2].summary
    assert items[2].tags == ["rockets", "launch"]

    markdown = newsletter_builder.render_markdown(
        items, newsletter_date=date(2025, 10, 12)
    )
    assert markdown.startswith("# Futuroptimist Newsletter — 2025-10-12\n")
    assert "Watch on YouTube" in markdown
    assert "(tags: rockets, launch)" in markdown
    assert "Gamma preview mission hits lab benches this week." in markdown

    limited = newsletter_builder.collect_items(video_root, statuses={"live"}, limit=2)
    assert [item.slug for item in limited] == ["20240301_gamma", "20240201_beta"]

    filtered = newsletter_builder.collect_items(
        video_root,
        statuses={"live"},
        since=date(2024, 2, 1),
    )
    assert [item.slug for item in filtered] == ["20240301_gamma", "20240201_beta"]


def test_collect_items_falls_back_to_placeholder_when_script_missing(
    tmp_path: Path,
) -> None:
    video_root = tmp_path / "video_scripts"
    video_root.mkdir()

    epsilon = video_root / "20240401_epsilon"
    epsilon.mkdir()
    _write_metadata(
        epsilon,
        {
            "title": "Epsilon Update",
            "publish_date": "2024-04-01",
            "status": "live",
        },
        script_text="# Epsilon\n",
    )
    (epsilon / "script.md").unlink()

    items = newsletter_builder.collect_items(video_root)
    assert items[0].summary == "Summary coming soon."


def test_main_writes_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    video_root = tmp_path / "video_scripts"
    video_root.mkdir()
    folder = video_root / "20240501_delta"
    folder.mkdir()
    _write_metadata(
        folder,
        {
            "title": "Delta Wrap",
            "publish_date": "2024-05-01",
            "status": "live",
            "summary": "Delta wrap summary.",
            "youtube_id": "DDD444",
        },
    )

    output = tmp_path / "newsletter.md"
    exit_code = newsletter_builder.main(
        [
            "--video-root",
            str(video_root),
            "--output",
            str(output),
            "--status",
            "live",
            "--date",
            "2025-10-15",
        ]
    )
    assert exit_code == 0

    text = output.read_text(encoding="utf-8")
    assert "Futuroptimist Newsletter — 2025-10-15" in text
    assert "Delta Wrap" in text

    captured = capsys.readouterr()
    assert f"Wrote {output}" in captured.out
