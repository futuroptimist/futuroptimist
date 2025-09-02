# Python before uv for docs workflow

- Date: 2025-09-02
- Author: codex
- Status: resolved

## What went wrong
The Docs Preview & Link Check workflow installed uv before selecting the Python version, so linkchecker targeted the runner's default interpreter.

## Root cause
`setup-uv` ran before `actions/setup-python`, causing dependencies to install for the wrong Python version.

## Impact
The docs workflow failed during link checking because linkchecker was missing for the configured Python.

## Actions to take
- Set up Python before running `astral-sh/setup-uv` so dependencies install for the active interpreter.
