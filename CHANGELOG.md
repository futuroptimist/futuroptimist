# Changelog

## 2025-08-24
- fix: validate svg3d shading factor to reject NaN and infinity.

## 2025-08-23
- fix: add missing workflow field to outage record to restore CI.
- fix: treat 'timed out' variants as failures in status_to_emoji.
- test: require outage entries to reference schema and fix missing pointer.
- chore: set up Python before installing dependencies in test workflow.
- fix: install dependencies in uv-managed venv to avoid permission errors.

## 2025-08-22
- chore: skip Codecov upload when token is missing to prevent CI failures.
