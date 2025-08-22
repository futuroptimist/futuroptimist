# Heatmap CI failure

- **Date:** 2025-08-22
- **Author:** codex-bot
- **Status:** fixed

## What went wrong
The scheduled "Rebuild 3-D heat-map" workflow failed when running `uv pip`.

## Root cause
`uv` was never installed, so the command exited with "uv: command not found".

## Impact
Heatmap SVGs were not regenerated on schedule.

## Actions to take
- Install `astral-sh/setup-uv` before invoking `uv pip`.
- Add a test to ensure the workflow includes this step.
