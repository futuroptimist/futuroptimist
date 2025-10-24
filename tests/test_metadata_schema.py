import json
import pathlib
from jsonschema import validate, ValidationError
import pytest

SCHEMA_PATH = pathlib.Path("schemas/video_metadata.schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

VIDEO_DIR = pathlib.Path("video_scripts")


def _iter_metadata_files(base: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p for p in base.rglob("metadata.json") if p.is_file())


def test_metadata_files_validate():
    metadata_files = _iter_metadata_files(VIDEO_DIR)
    assert (
        metadata_files
    ), "video_scripts should contain at least one metadata.json to validate"
    for meta_path in metadata_files:
        data = json.loads(meta_path.read_text())
        try:
            validate(instance=data, schema=SCHEMA)
        except ValidationError as e:
            raise AssertionError(f"{meta_path} failed schema validation: {e.message}")


def test_invalid_metadata_fails():
    bad = {"youtube_id": "123", "title": "t", "duration_seconds": -5}
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=SCHEMA)


def test_metadata_validation_error(monkeypatch, tmp_path):
    bad = tmp_path / "20250101_bad" / "metadata.json"
    bad.parent.mkdir()
    bad.write_text("{}")
    monkeypatch.setattr("tests.test_metadata_schema.VIDEO_DIR", tmp_path)
    with pytest.raises(AssertionError):
        test_metadata_files_validate()


def test_live_metadata_includes_publish_details():
    """Published videos should expose publish date, tags, and thumbnail paths."""

    failures: list[str] = []
    for meta_path in _iter_metadata_files(VIDEO_DIR):
        data = json.loads(meta_path.read_text())
        status = str(data.get("status", "")).lower()
        if status != "live":
            continue
        publish_date = str(data.get("publish_date", "")).strip()
        keywords = data.get("keywords") or []
        thumbnail = str(data.get("thumbnail", "")).strip()
        view_count = data.get("view_count")
        video_url = str(data.get("video_url", "")).strip()
        if (
            not publish_date
            or not keywords
            or not thumbnail
            or not isinstance(view_count, int)
            or view_count <= 0
            or not video_url
            or not video_url.startswith("https://")
        ):
            failures.append(str(meta_path))

    assert not failures, (
        "Published metadata must include publish_date, keywords, thumbnail,"
        " a positive view_count, and the final video_url as documented in"
        " INSTRUCTIONS.md Phase 8: " + ", ".join(failures)
    )


def test_live_metadata_thumbnails_are_urls() -> None:
    """Live entries should store canonical YouTube thumbnail URLs."""

    failures: list[str] = []
    for meta_path in _iter_metadata_files(VIDEO_DIR):
        data = json.loads(meta_path.read_text())
        if str(data.get("status", "")).lower() != "live":
            continue
        thumbnail = str(data.get("thumbnail", "")).strip()
        if not thumbnail or not thumbnail.startswith("https://"):
            failures.append(str(meta_path))

    assert not failures, (
        "Live metadata should record YouTube thumbnail URLs (https) as promised in "
        "INSTRUCTIONS.md; offending files: " + ", ".join(failures)
    )
