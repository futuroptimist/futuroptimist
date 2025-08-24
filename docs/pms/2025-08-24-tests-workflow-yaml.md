# Stray shell prompt broke tests workflow

- Date: 2025-08-24
- Author: codex
- Status: resolved

## What went wrong
The `Test Suite` workflow failed to run because `.github/workflows/02-tests.yml` contained leftover shell prompt text.

## Root cause
A previous edit accidentally appended the terminal prompt to the workflow file, making the YAML invalid.

## Impact
CI for pull requests and pushes could not execute tests, blocking merges.

## Actions to take
- Remove the stray line from the workflow file.
- Add a unit test that parses all workflow files to catch YAML syntax issues early.
