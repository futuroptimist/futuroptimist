"""Utilities for converting transcript segments into overlapping chunks."""

from __future__ import annotations

from collections.abc import Iterable

from .models import TranscriptChunk, TranscriptSegment
from .utils import build_cite_url

DEFAULT_TARGET_CHARS = 1000
DEFAULT_OVERLAP_CHARS = 100


def chunk_segments(
    video_id: str,
    segments: Iterable[TranscriptSegment],
    target_chars: int = DEFAULT_TARGET_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[TranscriptChunk]:
    """Group segments into overlapping text chunks suitable for RAG."""

    segment_list = list(segments)
    if not segment_list:
        return []

    chunks: list[TranscriptChunk] = []
    idx = 0
    chunk_index = 0
    while idx < len(segment_list):
        char_count = 0
        j = idx
        chunk_segments: list[TranscriptSegment] = []
        while j < len(segment_list) and char_count < target_chars:
            seg = segment_list[j]
            chunk_segments.append(seg)
            char_count += len(seg.text)
            j += 1
        if not chunk_segments:
            chunk_segments.append(segment_list[idx])
            j = idx + 1
        text = " ".join(seg.text for seg in chunk_segments).strip()
        start = chunk_segments[0].start
        end_seg = chunk_segments[-1]
        end = end_seg.start + end_seg.dur
        segment_ids = [seg.id for seg in chunk_segments]
        chunk = TranscriptChunk(
            id=f"{video_id}_chunk_{chunk_index}",
            text=text,
            start=start,
            end=end,
            segment_ids=segment_ids,
            cite_url=build_cite_url(video_id, start),
        )
        chunks.append(chunk)
        chunk_index += 1
        if j >= len(segment_list):
            break
        next_idx = j
        overlap_accum = 0
        m = j - 1
        while m >= idx and overlap_accum < overlap_chars:
            overlap_accum += len(segment_list[m].text)
            m -= 1
        if overlap_chars > 0:
            next_idx = max(idx + 1, m + 1)
        idx = next_idx
    return chunks


__all__ = ["DEFAULT_OVERLAP_CHARS", "DEFAULT_TARGET_CHARS", "chunk_segments"]
