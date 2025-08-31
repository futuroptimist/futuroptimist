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


def test_flags_github_pat_token() -> None:
    token = "github_pat_" + "A" * 22 + "_" + "B" * 59
    diff = "diff --git a/x b/x\n" "--- a/x\n" "+++ b/x\n" "@@\n" f"+token={token}\n"
    proc = run_scan(diff)
    assert proc.returncode == 1
    assert "Possible secrets detected" in proc.stderr
    assert token in proc.stderr


def test_flags_ssn_like_string() -> None:
    ssn = "123-45-6789"
    diff = "diff --git a/x b/x\n" "--- a/x\n" "+++ b/x\n" "@@\n" f"+ssn={ssn}\n"
    proc = run_scan(diff)
    assert proc.returncode == 1
    assert ssn in proc.stderr


def test_flags_credit_card_luhn() -> None:
    # Visa test number passes Luhn
    cc = "4111 1111 1111 1111"
    diff = "diff --git a/x b/x\n" "--- a/x\n" "+++ b/x\n" "@@\n" f"+card={cc}\n"
    proc = run_scan(diff)
    assert proc.returncode == 1
    assert "4111111111111111" in proc.stderr
