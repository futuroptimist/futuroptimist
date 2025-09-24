from pathlib import Path

import pytest
import yaml


WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def test_workflows_parse():
    for path in WORKFLOWS_DIR.glob("*.yml"):
        with path.open("r", encoding="utf-8") as f:
            yaml.safe_load(f)


def test_workflows_do_not_use_secrets_in_if():
    for path in WORKFLOWS_DIR.glob("*.yml"):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.strip().startswith("if:") and "secrets." in line:
                pytest.fail(
                    f"{path.name}:{lineno} uses secrets context in if expression"
                )
