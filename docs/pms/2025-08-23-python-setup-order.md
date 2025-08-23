# Python setup after uv caused test failure

- Date: 2025-08-23
- Author: codex
- Status: resolved

## What went wrong
The `Test Suite` workflow installed dependencies before Python 3.12 was configured, leaving
`pytest` and other packages unavailable.

## Root cause
`uv pip` ran against the runner's default Python, so the subsequent 3.12 interpreter had no
dependencies.

## Impact
CI failed immediately with `ModuleNotFoundError` when invoking `pytest`.

## Actions to take
- Set up Python before installing dependencies with `uv pip`.
