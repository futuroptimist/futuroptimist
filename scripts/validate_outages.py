"""Validate outage JSON files against the repository schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from collections.abc import Iterable
from typing import Any

from jsonschema import Draft7Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTAGES_DIR = REPO_ROOT / "outages"
SCHEMA_PATH = OUTAGES_DIR / "schema.json"


def _iter_outage_files() -> list[Path]:
    files: list[Path] = []
    for path in OUTAGES_DIR.rglob("*.json"):
        if path.resolve() == SCHEMA_PATH.resolve():
            continue
        files.append(path)
    files.sort()
    return files


def _load_schema() -> Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft7Validator(schema)


def _error_sort_key(error: ValidationError) -> tuple[tuple[int, str], ...]:
    def _normalise_part(part: Any) -> tuple[int, str]:
        if isinstance(part, int):
            return (0, f"{part:06d}")
        return (1, str(part))

    return tuple(_normalise_part(part) for part in error.path)


def _format_pointer(path: Iterable[Any]) -> str:
    pointer = "/".join(str(part) for part in path)
    return pointer or "<root>"


def validate_outages() -> list[str]:
    validator = _load_schema()
    errors: list[str] = []
    for path in _iter_outage_files():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
            continue
        for error in sorted(validator.iter_errors(data), key=_error_sort_key):
            location = f"{path}: {_format_pointer(error.path)}"
            errors.append(f"{location} – {error.message}")
    return errors


def main() -> int:
    errors = validate_outages()
    if errors:
        for message in errors:
            sys.stderr.write(f"{message}\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
