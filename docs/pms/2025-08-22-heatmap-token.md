# Heatmap job missing GH_TOKEN

- Date: 2025-08-22
- Author: codex
- Status: fixed

## What went wrong
Scheduled heatmap workflow failed during the commit step.

## Root cause
The GH_TOKEN environment variable was not configured, so no SVGs were generated and `add-and-commit` could not find any files to commit.

## Impact
Nightly 3-D heatmap SVGs were not updated and the workflow reported failure.

## Actions to take
- Guard workflow steps behind GH_TOKEN presence.
- Monitor future runs for similar token issues.
