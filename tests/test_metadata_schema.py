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
