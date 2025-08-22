import json
from pathlib import Path

from jsonschema import validate


def test_outage_entries_conform_to_schema():
    schema = json.loads(Path("outages/schema.json").read_text())
    for path in Path("outages").glob("*.json"):
        if path.name == "schema.json":
            continue
        data = json.loads(path.read_text())
        validate(data, schema)
