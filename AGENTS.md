# Futuroptimist – Agents.md Guide for AI Tools

> Welcome! This file orients both AI assistants and human contributors. Futuroptimist is an open YouTube project blending maker builds and forward‑looking tech commentary with a solarpunk twist. Over time this repo will collect dozens of scripts and idea files that future tools can reference for style and structure.

Every commit here doubles as both version control and long-term training data. Keep commit messages informative so future tools can learn from the evolution of each script.
Keep `llms.txt` synchronized with changes to this guide so LLMs stay current.

## Project Top-Level Layout

| Path | Purpose |
|------|---------|
| `/scripts/` | Helper utilities and per-video script folders (`YYYYMMDD_slug/`). Run `scaffold_videos.py` to fetch titles/dates and create them from `video_ids.txt`. |
| `/ideas/` | Checklist-style idea files – raw, WIP content. |
| `/schemas/` | JSON-Schemas (e.g. `video_metadata.schema.json`). |
| `/tests/` | Pytest suites; keep parity with production code. |
| `/Makefile` & `setup.ps1` | Developer automation (venv, tests, subtitles, render). |
| `/llms.txt` | Complementary file containing creative context & tone. |
| `/subtitles/` | Downloaded `.srt` caption files populated by `fetch_subtitles.py`. |
| `video_ids.txt` | Canonical list of YouTube IDs referenced by helper scripts. |
| `INSTRUCTIONS.md` | Extended setup steps and roadmap. |

## Coding Conventions

* Python 3.11+, black formatting & ruff lint (pre-commit soon).
* One logical change per PR; always include/extend tests.
* Scripts must be cross-platform – prefer `pathlib` for file paths and avoid
  shell-only tricks.

## Script Format

Video scripts (`scripts/YYYYMMDD_slug/script.md`) combine narration and stage
directions. Use `[NARRATOR]:` for spoken lines and `[VISUAL]:` for b-roll or
graphics cues. Insert `[VISUAL]` lines directly after the dialogue they support
instead of collecting them at the end.
- Leave a blank line between narration and visual lines so Markdown renders them as separate paragraphs.
- When importing transcripts from `.srt` files, strip prefix markers like `- [Narrator]` and split sentences into individual `[NARRATOR]` lines for clarity.
- Each script folder must include a `metadata.json` file conforming to `schemas/video_metadata.schema.json`.

## Testing & CI

Run all tests:

```bash
make setup   # venv + deps (or ./setup.ps1)
make test
```
If `make setup` fails on your platform, run `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` then `pytest -q`.
If `yt-dlp` cannot be located during tests, prefix your command with `PATH=.venv/bin:$PATH` so the venv's executables are discoverable.

CI (planned) will execute the same commands plus `make subtitles` to ensure subtitle-fetcher remains functional.

## Vision & Workflow

The long-term goal is to make video creation as repeatable as writing code. Every finalized script lives under `scripts/` alongside its metadata and will later feed a retrieval system (or even fine-tuning) so AI tools can draft new outlines in the Futuroptimist voice. Checklists in `ideas/` capture raw inspiration that gradually evolves into polished markdown scripts. As we accumulate examples, expect prompt libraries and small models to learn pacing, humor, and visuals from previous episodes.

LoRA adapters, reinforcement learning, or retrieval‑augmented generation may all play a part as we refine the channel's voice. Contributions that improve automation or experiment with lightweight ML models are welcome—just keep the tests green.

## Render & Publish (Future-Phase)

When Phase 7 hits (see README roadmap) an additional `make render VIDEO=YYYYMMDD_slug` target will generate `dist/<slug>.mp4`. Subsequent automation will call YouTube Data API for upload.

## Contribution Quick-Start

1. Fork & branch.
2. `make setup` then `make test`.
3. `python scripts/scaffold_videos.py` to pull metadata and create dated script folders from `video_ids.txt` (commit new folders).
4. Optionally run `make subtitles` to verify caption downloads.
5. Add or update code **and** matching tests.
6. Commit with descriptive message; open PR.

## Additional Resources (File List)

### Documentation
- [README](README.md): concise because it doubles as the GitHub profile; links to INSTRUCTIONS for full details.
- [INSTRUCTIONS](INSTRUCTIONS.md): full workflow and roadmap.
- [RUNBOOK](RUNBOOK.md): production checklist.
- [Ideas guide](ideas/README.md): idea-file schema.

### Schemas
- [Video Metadata Schema](schemas/video_metadata.schema.json): strict JSON schema for `metadata.json`.

Tests under `tests/` cover folder naming (`test_folder_names.py`), schema validation (`test_metadata_schema.py`) and the helper scripts. Extend them when adding new features.

### Optional
- [Contributors guide](CONTRIBUTORS.md): PR etiquette and code style details.

---
*For creative context, tone, and thematic constraints refer to [`llms.txt`](llms.txt).* 
