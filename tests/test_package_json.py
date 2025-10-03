from __future__ import annotations

import json
from pathlib import Path


def test_package_json_scripts_present() -> None:
    pkg_path = Path("package.json")
    assert pkg_path.exists(), "package.json must exist so npm run commands work"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    required = ["lint", "format:check", "test:ci"]
    for name in required:
        assert name in scripts, f"npm script '{name}' must be defined"
        assert str(scripts[name]).strip(), f"npm script '{name}' must not be empty"


def test_package_json_exposes_playwright_install_script() -> None:
    pkg_path = Path("package.json")
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    command = scripts.get("playwright:install")
    assert command, "npm script 'playwright:install' must be defined"
    assert command.strip() == "npx playwright install --with-deps"
