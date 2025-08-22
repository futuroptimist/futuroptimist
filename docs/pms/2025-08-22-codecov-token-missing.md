# Codecov token missing

- Date: 2025-08-22
- Author: codex
- Status: resolved

## What went wrong
The `Test Suite` workflow failed when the Codecov step tried to upload coverage
without a token.

## Root cause
Forked pull requests do not receive repository secrets, so the step ran with an
empty `CODECOV_TOKEN` and exited with an error.

## Impact
Test runs on external contributions reported failure even though the tests
passed.

## Actions to take
- Run coverage upload only when `CODECOV_TOKEN` is available.
- Ignore Codecov upload failures to keep CI green.
