"""Chunking utilities for transcripts."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Chunk, Segment


def _build_cite_url(video_id: str, start: float) -> str:
    seconds = max(0, int(start))
    return f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"


def chunk_segments(
    video_id: str,
    segments: Iterable[Segment],
    *,
    target_chars: int = 1000,
    overlap_chars: int = 100,
) -> list[Chunk]:
    """Group segments into overlapping text chunks."""

    chunk_list: list[Chunk] = []
    buffer: list[Segment] = []

    def flush() -> None:
        if not buffer:
            return
        text = " ".join(seg.text for seg in buffer).strip()
        if not text:
            buffer.clear()
            return
        segment_ids = [seg.id for seg in buffer]
        if chunk_list and chunk_list[-1].segment_ids == segment_ids:
            return
        start = buffer[0].start
        end = buffer[-1].start + buffer[-1].dur
        chunk_id = f"chunk_{len(chunk_list)+1:04d}"
        chunk_list.append(
            Chunk(
                id=chunk_id,
                text=text,
                start=start,
                end=end,
                segment_ids=segment_ids,
                cite_url=_build_cite_url(video_id, start),
            )
        )

    for segment in segments:
        if not segment.text.strip():
            continue
        buffer.append(segment)
        text = " ".join(seg.text for seg in buffer).strip()
        if len(text) >= target_chars:
            flush()
            if overlap_chars > 0:
                carry: list[Segment] = []
                count = 0
                for seg in reversed(buffer):
                    carry.insert(0, seg)
                    count += len(seg.text)
                    if count >= overlap_chars:
                        break
                buffer[:] = carry
            else:
                buffer.clear()

    flush()
    return chunk_list


__all__ = ["chunk_segments"]
