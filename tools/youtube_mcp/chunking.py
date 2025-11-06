"""Utilities for transcript chunking and normalisation."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Chunk, Segment
from .utils import build_watch_url


def chunk_segments(
    video_id: str,
    segments: Iterable[Segment],
    *,
    target_chars: int = 1000,
    overlap_chars: int = 100,
) -> list[Chunk]:
    """Chunk a transcript into retrieval-friendly windows."""

    segment_list = list(segments)
    if not segment_list:
        return []

    chunks: list[Chunk] = []
    current_segments: list[Segment] = []
    current_length = 0

    for segment in segment_list:
        seg_len = len(segment.text)
        if current_segments and current_length + seg_len > target_chars:
            chunks.append(_build_chunk(video_id, current_segments, len(chunks)))
            current_segments = _tail_with_overlap(current_segments, overlap_chars)
            current_length = sum(len(seg.text) for seg in current_segments)
        current_segments.append(segment)
        current_length += seg_len

    if current_segments:
        chunks.append(_build_chunk(video_id, current_segments, len(chunks)))

    return chunks


def _tail_with_overlap(segments: list[Segment], overlap_chars: int) -> list[Segment]:
    if not segments or overlap_chars <= 0:
        return []
    retained: list[Segment] = []
    total = 0
    for segment in reversed(segments):
        retained.insert(0, segment)
        total += len(segment.text)
        if total >= overlap_chars:
            break
    return retained


def _build_chunk(video_id: str, segments: list[Segment], index: int) -> Chunk:
    start = segments[0].start
    end = max(segment.start + segment.dur for segment in segments)
    text = " ".join(segment.text for segment in segments).strip()
    segment_ids = [segment.id for segment in segments]
    cite_url = f"{build_watch_url(video_id)}&t={int(start)}s"
    return Chunk(
        id=f"{video_id}:chunk:{index}",
        text=text,
        start=start,
        end=end,
        segment_ids=segment_ids,
        cite_url=cite_url,
    )
