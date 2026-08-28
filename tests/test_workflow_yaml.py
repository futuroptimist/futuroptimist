import re
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


def test_production_pdf_workflow_is_safe_and_dynamic() -> None:
    path = WORKFLOWS_DIR / "04-production-pdf.yml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    triggers = data.get("on") or data.get(True)
    assert list(triggers) == ["workflow_dispatch"]
    dispatch = triggers["workflow_dispatch"]["inputs"]
    assert dispatch["video_script"] == {
        "description": "Eligible video-script slug or latest",
        "required": True,
        "type": "string",
        "default": "latest",
    }
    assert dispatch["page_size"]["type"] == "choice"
    assert dispatch["page_size"]["options"] == ["letter", "a4"]
    assert dispatch["page_size"]["default"] == "letter"
    assert data["permissions"] == {"contents": "read"}
    assert "src/render_production_pdf.py" in text
    assert "REQUESTED_VIDEO_SCRIPT: ${{ inputs.video_script }}" in text
    assert "PAGE_SIZE: ${{ inputs.page_size }}" in text
    action_references = re.findall(r"uses:\s+([^\s#]+)", text)
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref) for ref in action_references)
    assert action_references == [
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ]
    assert "production-pdf-${{ steps.resolve.outputs.slug }}" in text
    assert "path: ${{ steps.resolve.outputs.output }}" in text
    assert 'f"{slug}-production-checklist.pdf"' in text
    assert "default: 20260901_sugarkube" not in text
