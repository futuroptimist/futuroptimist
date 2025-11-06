from tools.youtube_mcp.chunking import chunk_segments
from tools.youtube_mcp.models import Segment


def build_segment(idx: int, text: str, start: float, dur: float) -> Segment:
    return Segment(id=f"vid:{idx}", text=text, start=start, dur=dur)


def test_chunk_segments_overlap_and_citation():
    segments = [
        build_segment(0, "hello world", 0.0, 1.0),
        build_segment(1, "this is a test", 1.0, 1.0),
        build_segment(2, "more words to ensure chunking happens", 2.0, 1.0),
        build_segment(3, "final bit", 3.0, 1.0),
    ]
    chunks = chunk_segments("vid", segments, target_chars=25, overlap_chars=10)
    assert len(chunks) == 3
    assert chunks[0].cite_url.endswith("t=0s")
    assert chunks[1].segment_ids[0] == segments[1].id
    assert chunks[-1].text.endswith("final bit")


def test_chunk_segments_handles_empty_input():
    assert chunk_segments("vid", [], target_chars=10) == []


def test_chunk_segments_without_overlap():
    segments = [build_segment(0, "short", 0.0, 1.0), build_segment(1, "tiny", 1.0, 1.0)]
    chunks = chunk_segments("vid", segments, target_chars=5, overlap_chars=0)
    assert len(chunks) == 2
    assert chunks[1].segment_ids[0] == segments[1].id


def test_chunk_segments_large_overlap_keeps_all_segments():
    segments = [
        build_segment(0, "one", 0.0, 1.0),
        build_segment(1, "two", 1.0, 1.0),
    ]
    chunks = chunk_segments("vid", segments, target_chars=3, overlap_chars=100)
    assert len(chunks) == 2
    assert chunks[1].segment_ids == [segments[0].id, segments[1].id]
