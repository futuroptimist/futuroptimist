from pathlib import Path
import json
import jsonschema


def test_outages_conform_to_schema() -> None:
    schema = json.loads(Path("outages/schema.json").read_text())
    validator = jsonschema.Draft7Validator(schema)
    for path in Path("outages").glob("*.json"):
        if path.name == "schema.json":
            continue
        data = json.loads(path.read_text())
        validator.validate(data)
