# Update Repo Status workflow installing rawpy on Python 3.13

- **Date**: 2025-11-04
- **Summary**: The scheduled "Update Repo Statuses" workflow failed during dependency installation
  after GitHub Actions upgraded the default `python-version: 3.x` runtime to Python 3.13.
- **Root Cause**: `rawpy 0.25.1` has prebuilt wheels for Python ≤3.12. When the runner pulled Python
  3.13 the `uv pip install --system -r requirements.txt` step could only fall back to building from
  source, which is blocked in the hosted environment, so the step exited with an error.
- **Resolution**: Pin the workflow to Python 3.12 so uv installs the published wheels, restoring the
  automation run.
- **Lessons**: Avoid floating `3.x` runtimes for workflows that depend on third-party wheels; bump
  explicitly after confirming binary compatibility.
