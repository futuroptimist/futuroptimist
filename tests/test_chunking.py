"""Chunking logic tests."""

from __future__ import annotations

from itertools import pairwise

from tools.youtube_mcp.chunking import chunk_segments
from tools.youtube_mcp.models import TranscriptSegment


def make_segment(idx: int, text: str, start: float, dur: float) -> TranscriptSegment:
    return TranscriptSegment(id=f"seg{idx}", text=text, start=start, dur=dur)


def test_chunking_produces_overlap() -> None:
    segments = [
        make_segment(1, "This is the first sentence.", 0.0, 3.0),
        make_segment(2, "Another informative line follows.", 3.0, 3.0),
        make_segment(3, "Important context continues here.", 6.0, 3.0),
        make_segment(4, "Final thought wraps things up.", 9.0, 3.0),
    ]

    chunks = chunk_segments("demo", segments, target_chars=60, overlap_chars=20)

    assert len(chunks) >= 2
    for first, second in pairwise(chunks):
        assert set(first.segment_ids) & set(second.segment_ids)
    assert chunks[0].segment_ids[0] == segments[0].id
    assert chunks[-1].segment_ids[-1] == segments[-1].id
    assert chunks[0].cite_url.endswith("t=0s")
    assert chunks[1].cite_url.endswith("t=3s")
