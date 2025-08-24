from pathlib import Path

import yaml


WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def test_workflows_parse():
    for path in WORKFLOWS_DIR.glob("*.yml"):
        with path.open("r", encoding="utf-8") as f:
            yaml.safe_load(f)
