import subprocess
import sys
from pathlib import Path


def run_scan(content: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(Path("scripts/scan-secrets.py"))],
        input=content.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_no_secrets(tmp_path):
    proc = run_scan("hello world")
    assert proc.returncode == 0
    assert proc.stderr == b""


def test_detects_secret(tmp_path):
    proc = run_scan("api_key=12345")  # pragma: allowlist secret
    assert proc.returncode == 1
    assert b"api_key" in proc.stderr
