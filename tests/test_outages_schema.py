import json
from pathlib import Path

import jsonschema
from jsonschema import validate


def test_outages_conform_to_schema() -> None:
    schema = json.loads(Path("outages/schema.json").read_text())
    validator = jsonschema.Draft7Validator(schema)

    for path in Path("outages").glob("*.json"):
        if path.name == "schema.json":
            continue
        data = json.loads(path.read_text())

        # Use both methods to ensure schema compliance
        validator.validate(data)
        validate(data, schema)


def test_outages_reference_schema() -> None:
    for path in Path("outages").glob("*.json"):
        if path.name == "schema.json":
            continue
        data = json.loads(path.read_text())
        assert data.get("$schema") == "./schema.json"
