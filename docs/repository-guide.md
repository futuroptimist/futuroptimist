# Futuroptimist Repository Guide

This guide collects the repo-internal details that used to live in the profile README. Use it when you want to run automation, understand the project layout, or work on the YouTube production helpers behind the Futuroptimist channel.

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/futuroptimist/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/futuroptimist/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/futuroptimist/branch/main/graph/badge.svg)](https://app.codecov.io/gh/futuroptimist/futuroptimist/branch/main)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/futuroptimist/actions/workflows/03-docs.yml)

## Purpose

This repository hosts scripts, metadata, prompt guides, tests, and small services for the [Futuroptimist YouTube channel](https://www.youtube.com/@futuroptimist). The goal is to make video creation as repeatable as writing code: finalized scripts live beside structured metadata, footage checklists, sources, and automation that can later feed retrieval or lightweight ML experiments.

For end-to-end contributor setup and roadmap details, see [INSTRUCTIONS.md](../INSTRUCTIONS.md). AI-agent guidance lives in [AGENTS.md](../AGENTS.md), and the canonical Codex automation prompt lives in [docs/prompts/codex/automation.md](prompts/codex/automation.md).

## Map of the repo

**Navigate in three hops:**

1. **Setup** – Follow [INSTRUCTIONS.md](../INSTRUCTIONS.md) for `uv` environment steps and contributor onboarding.
2. **Run** – Explore the [Makefile](../Makefile) targets for day-to-day automation; CLI helpers live in [`src/`](../src).
3. **Test** – Execute `make test` or `python -m pytest -q` to run the pytest suite.

| Category | Path / resource | Notes |
|----------|----------------|-------|
| Packages | [`src/`](../src) | Shared Python modules and CLI entry points for subtitles, metadata, assets, rendering, analytics, and status updates. |
| Scripts | [`scripts/`](../scripts) | Operational helpers such as prompt migrations and safety checks. |
| Video scripts | [`video_scripts/`](../video_scripts) | Per-video folders named `YYYYMMDD_slug` with `script.md`, `metadata.json`, and optional `assets.json`, `sources.txt`, or `footage.md`. |
| Subtitles | [`subtitles/`](../subtitles) | Downloaded caption files populated by subtitle helpers. |
| Schemas | [`schemas/`](../schemas) | JSON Schemas for metadata and asset manifests. |
| Data | [`data/`](../data) | Lightweight generated/reference data used by prompt and retrieval helpers. |
| Docs | [`docs/`](.) | Prompt docs, playbooks, this guide, and supporting documentation. |
| Tests | [`tests/`](../tests) | Pytest suite mirroring production helpers. |
| Pipelines | [`outages/`](../outages) | Incident logs and schema describing stability. |
| Infra | [`.github/workflows/`](../.github/workflows) | CI for linting, tests, docs, and scheduled status updates. |

Prompt templates stay grouped under [`docs/prompts/codex/`](prompts/codex/) with an index in [`docs/README.md`](README.md). Local multimedia assets belong under a gitignored `footage/` directory and are indexed through Makefile helpers when available.

## Setup and common commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and `requirements.txt`.

```bash
make setup   # create .venv and install dependencies
make test    # run pytest through the venv
make fmt     # run black and ruff --fix
```

If `make setup` fails on your platform, run:

```bash
python3 -m venv .venv
uv pip install -r requirements.txt
python -m pytest -q
```

Useful direct commands:

```bash
uv sync
uv run pytest
uvx <tool>
python -m pytest -q
python -m pytest --cov=./src --cov=./tests
```

Before committing code changes, follow the repo guidance in [AGENTS.md](../AGENTS.md): format with Black/Ruff, run relevant tests, and scan staged changes with `git diff --cached | ./scripts/scan-secrets.py` when `scripts/scan-secrets.py` is present.

## Automation, scripts, metadata, and subtitles

- `src/scaffold_videos.py` creates dated `video_scripts/YYYYMMDD_slug/` folders from `video_ids.txt`.
- `src/fetch_subtitles.py` and Makefile target `make subtitles` download captions for known videos.
- `src/srt_to_markdown.py` converts `.srt` captions into the repo's script format with `[NARRATOR]:` lines and `[VISUAL]:` cues.
- `src/generate_scripts_from_subtitles.py` scans metadata and subtitles to produce `script.md` drafts.
- `src/update_video_metadata.py`, `src/enrich_metadata.py`, and related helpers refresh YouTube metadata when API credentials are available.
- `src/index_local_media.py`, `src/index_assets.py`, `src/generate_assets_manifest.py`, and `src/report_funnel.py` keep footage and asset manifests searchable without committing local media.
- `src/render_video.py`, `src/create_otio_timeline.py`, `src/prepare_youtube_upload.py`, and `src/upload_to_youtube.py` support render and publish workflows.
- `src/repo_status.py` updates the profile README's `## Related Projects` list by scanning parseable `- ` bullets containing GitHub repo URLs.

Video script folders should start with a title heading, include a YouTube ID blockquote and `## Script` section, and keep `metadata.json` valid against [`schemas/video_metadata.schema.json`](../schemas/video_metadata.schema.json). Use `sources.txt` for one URL per line and cite third-party references rather than redistributing downloaded content.

## YouTube Transcript MCP Service

`tools/youtube_mcp/` packages a transcript fetcher that powers a CLI, FastAPI microservice, and MCP-compatible stdio tool. It normalizes captions for retrieval, stores 14-day cached payloads in SQLite, and preserves provenance through timestamped cite URLs.

- **HTTP**: `python -m tools.youtube_mcp --host 127.0.0.1 --port 8765`
- **CLI**: `python -m tools.youtube_mcp.cli transcript --url https://youtu.be/VIDEOID`
- **MCP**: `python tools/youtube_mcp/mcp_server.py`

Example HTTP call:

```bash
curl "http://127.0.0.1:8765/transcript?url=https://youtu.be/VIDEOID"
```

**Policy notes**: the service only uses `youtube_transcript_api` and the public oEmbed endpoint, rejecting private or unlisted videos when signals are available. It never scrapes HTML or bypasses authentication walls.

**Caching**: responses are keyed by video ID, language, and track type with a default 14-day TTL; expired rows are purged automatically when accessed.

**Error codes**: `InvalidArgument`, `VideoUnavailable`, `NoCaptionsAvailable`, `PolicyRejected`, `RateLimited`, and `NetworkError` map to consistent HTTP responses and MCP error payloads.

## More documentation

- [INSTRUCTIONS.md](../INSTRUCTIONS.md) – full workflow and roadmap.
- [RUNBOOK.md](../RUNBOOK.md) – production checklist.
- [docs/video-editing-playbook.md](video-editing-playbook.md) – structure, pacing, and post-production notes.
- [docs/README.md](README.md) – documentation index.
