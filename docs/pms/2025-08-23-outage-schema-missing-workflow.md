# 2025-08-23 – Missing workflow field in outage record

- Date: 2025-08-23
- Author: codex
- Status: fixed

## What went wrong
The test suite failed because an outage entry violated the documented schema.

## Root cause
`outages/2025-08-22-missing-gh-token.json` omitted the required `workflow` field, triggering schema validation errors.

## Impact
GitHub Actions `02-tests` workflow failed on the default branch, blocking merges.

## Actions to take
- Validate new outage entries locally before committing.
- Consider automation to lint outage files in pre-commit.
