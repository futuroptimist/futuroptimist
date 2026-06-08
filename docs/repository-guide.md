# Repository Guide

This document keeps repository-specific operations out of the profile-first `README.md`. Use it when you need to understand the Futuroptimist production workspace: automation, scripts, metadata, subtitles, source collection, local indexes, and the YouTube Transcript MCP service.

## CI and project status

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/futuroptimist/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/futuroptimist/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/futuroptimist/branch/main/graph/badge.svg)](https://app.codecov.io/gh/futuroptimist/futuroptimist/branch/main)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/futuroptimist/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/futuroptimist)](../LICENSE)

The automated tests run via GitHub Actions on each push and pull request. Contributor setup details live in [`INSTRUCTIONS.md`](../INSTRUCTIONS.md), AI-agent guidance lives in [`AGENTS.md`](../AGENTS.md), and the canonical Codex automation prompt lives in [`docs/prompts/codex/automation.md`](prompts/codex/automation.md).

## Map of the repo

**Navigate in three hops:**

1. **Setup** – Follow [`INSTRUCTIONS.md`](../INSTRUCTIONS.md) for `uv` environment steps and contributor onboarding.
2. **Run** – Explore the [`Makefile`](../Makefile) targets for day-to-day automation; CLI helpers live in [`src/`](../src).
3. **Test** – Execute `make test` (documented in `INSTRUCTIONS.md`) to run the full pytest suite with coverage.

| Category | Path / resource | Notes |
|----------|----------------|-------|
| Apps | _n/a_ | Entry points live in `src/`; no standalone services yet. |
| Packages | [`src/`](../src) | Shared Python modules and CLI entry points. |
| Scripts | [`scripts/`](../scripts) | Operational helpers such as prompt migrations and credential checks. |
| Data | [`data/prompt-docs/`](../data/prompt-docs) | Lightweight reference lists synced with docs. |
| Docs | [`docs/`](.) | Prompts, playbooks, this repository guide, and supporting guides. |
| Tests | [`tests/`](../tests) | Pytest suite mirroring production helpers. |
| Pipelines | [`outages/`](../outages) | Incident logs and schema describing stability. |
| Infra | [`.github/workflows/`](../.github/workflows) | CI for lint, tests, docs, and status updates. |

Prompt templates stay grouped under [`docs/prompts/codex/`](prompts/codex/) with an index in [`docs/README.md`](README.md). Video narration lives in [`video_scripts/`](../video_scripts), and multimedia assets are catalogued through the index targets described below.

## Setup and day-to-day commands

The repo manages Python dependencies with [`uv`](https://docs.astral.sh/uv/). The Makefile auto-detects Windows vs Unix paths, so the standard flow is:

```bash
make setup   # venv + deps (or ./setup.ps1)
make test    # runs pytest -q
```

Useful alternatives and recovery commands:

```bash
uv sync
uv run pytest
pytest --cov=./src --cov=./tests
python3 -m venv .venv && uv pip install -r requirements.txt && pytest -q
PATH=.venv/bin:$PATH pytest -q
```

If `yt-dlp` cannot be located during tests, prefix the command with `PATH=.venv/bin:$PATH` so the virtual environment's executables are discoverable.

Before committing code changes, run formatting, linting, tests, and the staged credential scanner described in [`AGENTS.md`](../AGENTS.md):

```bash
black .
ruff check --fix .
git diff --cached | ./scripts/scan-secrets.py
```

## Video scripts, metadata, and subtitles

Per-video production folders live under `video_scripts/YYYYMMDD_slug/` and typically contain:

- `script.md` with `[NARRATOR]:` spoken lines and `[VISUAL]:` supporting cues.
- `metadata.json` conforming to [`schemas/video_metadata.schema.json`](../schemas/video_metadata.schema.json).
- Optional `assets.json` conforming to [`schemas/assets_manifest.schema.json`](../schemas/assets_manifest.schema.json).
- Optional `sources.txt` for one URL per reference source.
- Optional `footage.md` checklists for archive footage, new shots, CGI, or generative segments.

Subtitles are downloaded into [`subtitles/`](../subtitles) and can be converted with [`src/srt_to_markdown.py`](../src/srt_to_markdown.py). The converter handles italics, bold, emoji, HTML stripping, speaker-prefix cleanup, whitespace normalization, and non-dialogue cues such as `[Music]`.

Useful helpers include:

- `python src/scaffold_videos.py` to fetch titles/dates and create script folders from [`video_ids.txt`](../video_ids.txt).
- `make subtitles` to download captions when needed.
- `python src/update_transcript_links.py` to sync `transcript_file` paths and, with `YOUTUBE_API_KEY`, fetch missing captions through the YouTube Data API.
- `python src/update_video_metadata.py` or `python src/enrich_metadata.py` to refresh titles, publish dates, durations, thumbnails, tags, descriptions, view counts, and related metadata.
- `python src/collect_sources.py` to populate reference files from [`source_urls.txt`](../source_urls.txt) and per-video `sources.txt` files. Downloaded articles or clips are for reference only; cite sources in APA style rather than redistributing content.

## Local media and asset indexes

Large photos or video files belong in a local `footage/` folder, which is ignored by git. Rebuild indexes whenever local assets change:

```bash
make index_footage  # writes footage_index.json (git-ignored)
make index_assets   # writes assets_index.json (git-ignored)
```

The relevant helpers are:

- [`src/index_local_media.py`](../src/index_local_media.py) for a flat `footage_index.json` with paths, modification times, and sizes. Use `--exclude PATH` repeatedly to skip files or folders.
- [`src/index_assets.py`](../src/index_assets.py) for a richer `assets_index.json` based on per-video manifests, labels, optional notes paths, tags, and capture dates.
- [`src/index_script_segments.py`](../src/index_script_segments.py) to export `[NARRATOR]` segments for embeddings and retrieval.
- [`src/index_script_embeddings.py`](../src/index_script_embeddings.py) to hash narrator segments into deterministic vectors for local RAG tests.

## Render and publish workflow

Use `make render VIDEO=YYYYMMDD_slug` (optionally `CAPTIONS=path`) to concatenate converted clips with [`src/render_video.py`](../src/render_video.py) and write `dist/<slug>.mp4`. The workflow burns in subtitles when available and mirrors regression coverage in [`tests/test_render_video.py`](../tests/test_render_video.py).

Publishing helpers include metadata preparation, YouTube upload automation, analytics ingestion, and post-publish annotation. See [`INSTRUCTIONS.md`](../INSTRUCTIONS.md) for the fuller production checklist and roadmap.

## YouTube Transcript MCP Service

`tools/youtube_mcp/` packages a transcript fetcher that powers a CLI, FastAPI microservice, and MCP-compatible stdio tool. It normalizes captions for retrieval, stores 14-day cached payloads in SQLite, and preserves provenance via timestamped cite URLs.

- **HTTP**: `python -m tools.youtube_mcp --host 127.0.0.1 --port 8765`
- **CLI**: `python -m tools.youtube_mcp.cli transcript --url https://youtu.be/VIDEOID`
- **MCP**: `python tools/youtube_mcp/mcp_server.py`

Example HTTP call:

```bash
curl "http://127.0.0.1:8765/transcript?url=https://youtu.be/VIDEOID"
```

**Policy notes**: the service only uses `youtube_transcript_api` and the public oEmbed endpoint, rejecting private/unlisted videos when signals are available. It never scrapes HTML or bypasses authentication walls.

**Caching**: responses are keyed by video ID, language, and track type with a default 14-day TTL; expired rows are purged automatically when accessed.

**Error codes**: `InvalidArgument`, `VideoUnavailable`, `NoCaptionsAvailable`, `PolicyRejected`, `RateLimited`, and `NetworkError` map to consistent HTTP responses and MCP error payloads.
