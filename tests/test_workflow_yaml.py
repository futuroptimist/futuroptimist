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


def test_run_checks_invokes_actionlint() -> None:
    script = Path("scripts/npm/run-checks.mjs").read_text(encoding="utf-8")
    assert "actionlint" in script, "run-checks.mjs must invoke actionlint"
    assert (
        "createLinter" in script
    ), "run-checks.mjs should load actionlint's WASM linter"


def test_update_repo_status_pins_python_version() -> None:
    path = WORKFLOWS_DIR / "update-repo-status.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    steps = data["jobs"]["update"]["steps"]
    versions = [
        step["with"]["python-version"]
        for step in steps
        if step.get("uses") == "actions/setup-python@v5"
    ]
    assert versions == [
        "3.12"
    ], "update-repo-status workflow must pin Python 3.12 to keep rawpy wheels available"
