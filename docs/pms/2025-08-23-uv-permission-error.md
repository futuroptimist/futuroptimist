# uv --system install lacked permissions in CI

- Date: 2025-08-23
- Author: codex
- Status: resolved

## What went wrong
The `Test Suite` workflow tried installing packages to the system interpreter with
`uv pip --system`, which failed due to restricted write access on the hosted runner.

## Root cause
GitHub runners prevent writes to system Python directories, so `uv pip --system`
could not place dependencies.

## Impact
CI stopped during dependency installation before tests executed.

## Actions to take
- Create a uv-managed virtualenv and install dependencies within it.
