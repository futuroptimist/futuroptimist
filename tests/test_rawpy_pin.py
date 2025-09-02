from pathlib import Path

import pytest


def test_rawpy_pinned() -> None:
    """Ensure rawpy is pinned to a prebuilt version."""
    reqs = Path("requirements.txt").read_text().splitlines()
    for line in reqs:
        if line.startswith("rawpy"):
            assert line.strip() == "rawpy==0.25.1"
            break
    else:  # pragma: no cover - executed only if rawpy missing
        pytest.fail("rawpy not listed in requirements.txt")
