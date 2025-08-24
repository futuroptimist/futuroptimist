import subprocess
import sys


def run_scan(diff: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/scan-secrets.py"],
        input=diff,
        capture_output=True,
        text=True,
    )


def test_flags_github_token() -> None:
    token = "ghp_" + "0123456789abcdef0123456789abcdef0123"
    diff = "diff --git a/x b/x\n" "--- a/x\n" "+++ b/x\n" "@@\n" f"+token={token}\n"
    proc = run_scan(diff)
    assert proc.returncode == 1
    assert "Possible secrets detected" in proc.stderr
    assert token in proc.stderr
