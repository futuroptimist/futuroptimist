# Futuroptimist Repository Guide

This repository is the working hub behind the Futuroptimist YouTube/GitHub
project. The profile README stays intentionally lightweight; this guide collects
the repo-specific map, setup pointers, automation notes, and local service
details for contributors and AI tools.

## What lives here

The repo hosts scripts, metadata, captions, references, and helper automation for
turning maker experiments and forward-looking tech essays into repeatable video
production workflows. The long-form workflow and roadmap remain in
[`INSTRUCTIONS.md`](../INSTRUCTIONS.md), while day-to-day commands are exposed
through the [`Makefile`](../Makefile).

## Map of the repo

**Navigate in three hops:**

1. **Setup** – Follow [`INSTRUCTIONS.md`](../INSTRUCTIONS.md) for `uv`
   environment steps and contributor onboarding.
2. **Run** – Explore the [`Makefile`](../Makefile) targets for day-to-day
   automation; CLI helpers live in [`src/`](../src).
3. **Test** – Execute `make test` (documented in `INSTRUCTIONS.md`) to run the
   full pytest suite with coverage.

| Category | Path / resource | Notes |
|----------|----------------|-------|
| Apps | _n/a_ | Entry points live in `src/`; no standalone app ships from this repo. |
| Packages | [`src/`](../src) | Shared Python modules and CLI entry points. |
| Scripts | [`scripts/`](../scripts) | Operational helpers such as prompt migrations and safety checks. |
| Data | [`data/prompt-docs/`](../data/prompt-docs) | Lightweight reference lists synced with docs. |
| Docs | [`docs/`](.) | Prompts, playbooks, and supporting guides. |
| Tests | [`tests/`](../tests) | Pytest suite mirroring production helpers. |
| Pipelines | [`outages/`](../outages) | Incident logs and schema describing stability. |
| Infra | [`.github/workflows/`](../.github/workflows) | CI for lint, tests, docs, and status updates. |

Prompt templates stay grouped under
[`docs/prompts/codex/`](prompts/codex/) with an index in
[`docs/README.md`](README.md). Video narration lives in
[`video_scripts/`](../video_scripts), and multimedia assets are catalogued with
local indexers rather than committed media files.

## Setup and automation pointers

This repo manages Python dependencies with
[`uv`](https://docs.astral.sh/uv/). Use the detailed setup flow in
[`INSTRUCTIONS.md`](../INSTRUCTIONS.md); the short version is:

```bash
make setup   # venv + deps (or ./setup.ps1 on Windows)
make test    # runs pytest -q
make fmt     # black + ruff check --fix
```

The Makefile auto-detects Windows vs. Unix virtualenv paths. If `make setup`
fails on your platform, run `python3 -m venv .venv && uv pip install -r
requirements.txt`, then `pytest -q`. If tests cannot locate `yt-dlp`, prefix the
command with `PATH=.venv/bin:$PATH` so venv executables are visible.

Useful automation families include:

- `make subtitles` to populate downloaded `.srt` captions when needed.
- `python src/collect_sources.py` to fetch reference URLs into `sources/`.
- `make index_footage` to rebuild the gitignored `footage_index.json` from local
  media under `footage/`.
- `make index_assets` to rebuild the gitignored `assets_index.json` from
  per-video manifests.
- `make render VIDEO=YYYYMMDD_slug` to concatenate converted clips and optional
  captions into `dist/<slug>.mp4`.

## Scripts, metadata, subtitles, and assets

Video scripts live under `video_scripts/YYYYMMDD_slug/`. Each folder should
include a `metadata.json` file that conforms to
[`schemas/video_metadata.schema.json`](../schemas/video_metadata.schema.json).
Optional files such as `sources.txt`, `footage.md`, and `assets.json` enrich the
production pipeline without forcing large media into git.

Important helpers include:

- [`src/srt_to_markdown.py`](../src/srt_to_markdown.py) converts `.srt` captions
  into the Futuroptimist script format, using `[NARRATOR]:` for spoken lines and
  `[VISUAL]:` for supporting b-roll or graphics cues.
- [`src/generate_scripts_from_subtitles.py`](../src/generate_scripts_from_subtitles.py)
  resolves subtitle files from video metadata and produces `script.md` files.
- [`src/update_transcript_links.py`](../src/update_transcript_links.py) syncs
  `transcript_file` paths and can fetch missing captions when `YOUTUBE_API_KEY`
  is set.
- [`src/update_video_metadata.py`](../src/update_video_metadata.py) refreshes
  title, date, duration, tags, descriptions, thumbnails, and view counts via the
  YouTube Data API.
- [`src/index_script_segments.py`](../src/index_script_segments.py) exports
  `[NARRATOR]` segments for retrieval workflows.
- [`src/index_script_embeddings.py`](../src/index_script_embeddings.py) hashes
  script segments into deterministic local vectors for RAG tests.
- [`src/index_local_media.py`](../src/index_local_media.py) and
  [`src/index_assets.py`](../src/index_assets.py) build local media indexes from
  `footage/` and per-video manifests.

Large photos and videos belong in a local `footage/` directory, which is ignored
by git. Reference files downloaded by `collect_sources.py` are for citation and
review only; check rights before reuse and cite sources in APA style rather than
redistributing third-party material.

## YouTube Transcript MCP Service

`tools/youtube_mcp/` packages a transcript fetcher that powers a CLI, FastAPI
microservice, and MCP-compatible stdio tool. It normalizes captions for
retrieval, stores 14-day cached payloads in SQLite, and preserves provenance via
timestamped cite URLs.

- **HTTP**: `python -m tools.youtube_mcp --host 127.0.0.1 --port 8765`
- **CLI**: `python -m tools.youtube_mcp.cli transcript --url https://youtu.be/VIDEOID`
- **MCP**: `python tools/youtube_mcp/mcp_server.py`

Example HTTP call:

```bash
curl "http://127.0.0.1:8765/transcript?url=https://youtu.be/VIDEOID"
```

**Policy notes**: the service only uses `youtube_transcript_api` and the public
oEmbed endpoint, rejecting private or unlisted videos when signals are available.
It never scrapes HTML or bypasses authentication walls.

**Caching**: responses are keyed by video ID, language, and track type with a
default 14-day TTL; expired rows are purged automatically when accessed.

**Error codes**: `InvalidArgument`, `VideoUnavailable`, `NoCaptionsAvailable`,
`PolicyRejected`, `RateLimited`, and `NetworkError` map to consistent HTTP
responses and MCP error payloads.

## Testing and CI

GitHub Actions installs dependencies and runs lint, tests, docs checks, and
status updates. Locally, prefer focused checks first and then the repo-standard
suite:

```bash
python -m pytest tests/test_repo_status.py -q
python -m pytest -q
npm run docs-lint
```

If `npm run docs-lint` is unavailable because Node dependencies are not
installed, report that environment limit rather than treating the check as
passed.
