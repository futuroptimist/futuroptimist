"""Transcript normalization and chunking utilities."""
from __future__ import annotations

from typing import Iterable, List

from .models import TranscriptChunk, TranscriptSegment
from .utils import build_cite_url


def chunk_segments(
    video_id: str,
    segments: Iterable[TranscriptSegment],
    *,
    target_chars: int = 1000,
    overlap_chars: int = 100,
) -> List[TranscriptChunk]:
    """Chunk segments into retrieval-friendly windows.

    Segments are combined until ``target_chars`` is exceeded, ensuring each
    chunk contains at least one segment. The next chunk restarts from a segment
    boundary that recreates approximately ``overlap_chars`` of textual overlap.
    """

    normalized = list(segments)
    if not normalized:
        return []

    chunks: List[TranscriptChunk] = []
    start_idx = 0
    total_segments = len(normalized)

    while start_idx < total_segments:
        end_idx = start_idx
        current_text_parts: List[str] = []
        while end_idx < total_segments:
            seg = normalized[end_idx]
            candidate_text = " ".join([*current_text_parts, seg.text]).strip()
            current_text_parts.append(seg.text)
            end_idx += 1
            if len(candidate_text) >= target_chars and len(current_text_parts) > 1:
                break
        chunk_segments = normalized[start_idx:end_idx]
        chunk_text = " ".join(part for part in current_text_parts if part).strip()
        start_time = chunk_segments[0].start
        end_time = chunk_segments[-1].start + chunk_segments[-1].dur
        chunk_id = f"{video_id}-chunk-{len(chunks)+1:04d}"
        chunks.append(
            TranscriptChunk(
                id=chunk_id,
                text=chunk_text,
                start=start_time,
                end=end_time,
                segment_ids=[seg.id for seg in chunk_segments],
                cite_url=build_cite_url(video_id, start_time),
            )
        )

        if end_idx >= total_segments:
            break

        overlap_count = 0
        new_start = end_idx
        while new_start > start_idx and overlap_count < overlap_chars:
            new_start -= 1
            overlap_count += len(normalized[new_start].text) + 1

        # Guarantee forward progress even when the desired overlap would rewind
        # to the same start index. This can happen when ``overlap_chars`` is
        # larger than the accumulated text for the chunk. Without this guard the
        # loop would repeat with the same ``start_idx`` and never terminate.
        if new_start == start_idx:
            start_idx = min(end_idx, start_idx + 1)
        else:
            start_idx = new_start

    return chunks
