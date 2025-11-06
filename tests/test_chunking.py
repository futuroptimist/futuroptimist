from __future__ import annotations

from tools.youtube_mcp.chunking import chunk_segments
from tools.youtube_mcp.models import Segment


def make_segment(idx: int, text: str, start: float, dur: float) -> Segment:
    return Segment(id=f"seg_{idx:04d}", text=text, start=start, dur=dur)


def test_chunk_segments_produces_overlap() -> None:
    segments = [
        make_segment(0, "hello world", 0.0, 2.0),
        make_segment(1, "this is a test", 2.0, 2.0),
        make_segment(2, "chunking keeps overlap", 4.0, 2.0),
        make_segment(3, "final bit", 6.0, 2.0),
    ]
    chunks = chunk_segments(
        "abcdefghijk",
        segments,
        target_chars=30,
        overlap_chars=10,
    )
    assert len(chunks) == 2
    assert chunks[0].segment_ids == ["seg_0000", "seg_0001", "seg_0002"]
    assert chunks[1].segment_ids == ["seg_0002", "seg_0003"]
    assert chunks[0].cite_url.endswith("t=0s")
    assert chunks[1].cite_url.endswith("t=4s")
