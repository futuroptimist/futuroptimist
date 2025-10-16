"""Generate deterministic embeddings for Futuroptimist script segments.

This fulfils the Phase 3 "Script Intelligence" roadmap item in INSTRUCTIONS.md
that promised semantic embeddings under ``data/index``. The exporter reads the
segment index produced by :mod:`src.index_script_segments` and writes hashed
float vectors that downstream tooling can use as lightweight stand-ins for real
model embeddings during local development and CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from hashlib import blake2b
from typing import Iterable

DEFAULT_SEGMENTS_PATH = pathlib.Path("data/script_segments.json")
DEFAULT_OUTPUT_PATH = pathlib.Path("data/index/script_embeddings.json")
DEFAULT_DIMENSIONS = 12
MAX_DIMENSIONS = 16


def _load_segments(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Segments file {path} not found. Run src.index_script_segments first."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Failed to parse segments JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("Segments payload must be a JSON list of objects.")
    return data


def _normalize_chunks(chunks: Iterable[bytes]) -> list[float]:
    values: list[float] = []
    for chunk in chunks:
        if len(chunk) != 4:  # pragma: no cover - impossible with current usage
            raise ValueError("Digest chunks must be exactly 4 bytes long.")
        raw = int.from_bytes(chunk, byteorder="big", signed=False)
        # Map the integer into [-1.0, 1.0]. Use rounding to keep JSON compact.
        scaled = (raw / 0xFFFFFFFF) * 2 - 1
        values.append(round(scaled, 6))
    return values


def _embed_text(text: str, *, dimensions: int) -> list[float]:
    if dimensions <= 0:
        raise ValueError("dimensions must be positive.")
    if dimensions > MAX_DIMENSIONS:
        raise ValueError(
            f"dimensions cannot exceed {MAX_DIMENSIONS} (got {dimensions})."
        )
    digest_size = dimensions * 4
    digest = blake2b(text.encode("utf-8"), digest_size=digest_size).digest()
    chunks = (digest[idx : idx + 4] for idx in range(0, digest_size, 4))
    return _normalize_chunks(chunks)


def _isoformat_now() -> str:
    return (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_embeddings(
    *,
    segments_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
    dimensions: int = DEFAULT_DIMENSIONS,
) -> dict:
    """Return embedding payload and optionally write it to disk."""

    segments_path = segments_path.resolve()
    records = _load_segments(segments_path)

    enriched: list[dict] = []
    for record in records:
        text = record.get("text", "")
        embedding = _embed_text(text, dimensions=dimensions)
        enriched.append({**record, "embedding": embedding})

    payload = {
        "generated_at": _isoformat_now(),
        "dimensions": dimensions,
        "model": f"hash-blake2b-{dimensions}d",
        "segments": enriched,
    }

    if output_path is None:
        output_path = DEFAULT_OUTPUT_PATH
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate hashed embeddings for Futuroptimist script segments.",
    )
    parser.add_argument(
        "--segments",
        type=pathlib.Path,
        default=DEFAULT_SEGMENTS_PATH,
        help="Path to data/script_segments.json",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Destination JSON path (defaults to data/index/script_embeddings.json)",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_DIMENSIONS,
        help=f"Number of embedding dimensions (1-{MAX_DIMENSIONS})",
    )
    args = parser.parse_args(argv)

    try:
        build_embeddings(
            segments_path=args.segments,
            output_path=args.output,
            dimensions=args.dimensions,
        )
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
        return 2  # pragma: no cover - parser.error exits
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
