from __future__ import annotations

from tools.youtube_mcp.chunking import chunk_segments
from tools.youtube_mcp.models import TranscriptSegment


def make_segment(idx: int, text: str, start: float, dur: float) -> TranscriptSegment:
    return TranscriptSegment(id=f"seg-{idx}", text=text, start=start, dur=dur)


def test_chunk_segments_overlap() -> None:
    segments = [
        make_segment(1, "This is the first sentence.", 0.0, 3.0),
        make_segment(2, "Second sentence carries on the thought.", 3.0, 4.0),
        make_segment(3, "Third sentence closes it out.", 7.0, 4.0),
    ]

    chunks = chunk_segments("video123", segments, target_chars=45, overlap_chars=20)

    assert len(chunks) == 2
    assert chunks[0].segment_ids == ["seg-1", "seg-2"]
    assert chunks[1].segment_ids[-1] == "seg-3"
    assert chunks[0].cite_url.endswith("t=0s")
    assert chunks[1].cite_url.endswith("t=3s")
    assert chunks[0].end > chunks[0].start
    assert chunks[1].start <= chunks[0].end
