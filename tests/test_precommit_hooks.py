from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _iter_hooks() -> list[dict]:
    config_path = Path(".pre-commit-config.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    hooks: list[dict] = []
    for repo in data.get("repos", []):
        for hook in repo.get("hooks", []) or []:
            hook_copy = dict(hook)
            hook_copy.setdefault("repo", repo.get("repo"))
            hooks.append(hook_copy)
    return hooks


def test_precommit_validates_outage_json() -> None:
    hooks = _iter_hooks()
    matches = [
        hook
        for hook in hooks
        if hook.get("entry") == "python scripts/validate_outages.py"
    ]
    assert matches, "Add pre-commit hook to validate outage JSON files"
    assert matches[0].get("id"), "Pre-commit hook must declare an id"


def test_validate_outages_script_runs() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/validate_outages.py"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
