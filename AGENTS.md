# Futuroptimist – Agents.md Guide for AI Tools

> This Agents.md provides structured guidance for OpenAI Codex, Cursor, and any AI agents when navigating and contributing to the Futuroptimist repository.

## Project Top-Level Layout

| Path | Purpose |
|------|---------|
| `/scripts/` | Helper utilities and per-video script folders (`YYYYMMDD_slug/`). |
| `/ideas/` | Checklist-style idea files – raw, WIP content. |
| `/schemas/` | JSON-Schemas (e.g. `video_metadata.schema.json`). |
| `/tests/` | Pytest suites; keep parity with production code. |
| `/Makefile` & `setup.ps1` | Developer automation (venv, tests, subtitles, render). |
| `/llms.txt` | Complementary file containing creative context & tone. |
| `/subtitles/` | Downloaded `.srt` caption files populated by `fetch_subtitles.py`. |
| `video_ids.txt` | Canonical list of YouTube IDs referenced by helper scripts. |

## Coding Conventions

* Python 3.11+, black formatting & ruff lint (pre-commit soon).
* One logical change per PR; always include/extend tests.
* Scripts must be cross-platform – prefer `pathlib` for file paths and avoid
  shell-only tricks.

## Testing & CI

Run all tests:

```bash
make setup   # venv + deps (or ./setup.ps1)
make test
```
If `make setup` fails on your platform, run `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` then `pytest -q`.

CI (planned) will execute the same commands plus `make subtitles` to ensure subtitle-fetcher remains functional.

## Render & Publish (Future-Phase)

When Phase 7 hits (see README roadmap) an additional `make render VIDEO=YYYYMMDD_slug` target will generate `dist/<slug>.mp4`. Subsequent automation will call YouTube Data API for upload.

## Contribution Quick-Start

1. Fork & branch.
2. `make setup` then `make test`.
3. Optionally run `make subtitles` to verify caption downloads.
4. Add or update code **and** matching tests.
5. Commit with descriptive message; open PR.

## Additional Resources (File List)

### Documentation
- [README](README.md): onboarding & roadmap.
- [RUNBOOK](RUNBOOK.md): production checklist.
- [Ideas guide](ideas/README.md): idea-file schema.

### Schemas
- [Video Metadata Schema](schemas/video_metadata.schema.json): strict JSON schema for `metadata.json`.

Tests under `tests/` cover folder naming (`test_folder_names.py`), schema validation (`test_metadata_schema.py`) and the helper scripts. Extend them when adding new features.

### Optional
- [Contributors guide](CONTRIBUTORS.md): PR etiquette and code style details.

---
*For creative context, tone, and thematic constraints refer to [`llms.txt`](llms.txt).* 