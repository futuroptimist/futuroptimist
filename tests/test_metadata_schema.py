import json
import pathlib
from jsonschema import validate, ValidationError
import pytest

SCHEMA_PATH = pathlib.Path("schemas/video_metadata.schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

VIDEO_DIR = pathlib.Path("scripts")


def test_metadata_files_validate():
    for meta_path in VIDEO_DIR.glob("*/metadata.json"):
        data = json.loads(meta_path.read_text())
        try:
            validate(instance=data, schema=SCHEMA)
        except ValidationError as e:
            raise AssertionError(f"{meta_path} failed schema validation: {e.message}")


def test_invalid_metadata_fails():
    bad = {"youtube_id": "123", "title": "t", "duration_seconds": -5}
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=SCHEMA)
