# Futuroptimist Repository Guide

This repository is the working production hub for the Futuroptimist YouTube/GitHub project. The public `README.md` stays profile-first; this guide collects the repo-internal map, setup pointers, automation notes, metadata workflow, subtitle tooling, and YouTube Transcript MCP service details.

## Repository purpose

The repo hosts scripts, metadata, prompt docs, test fixtures, and production checklists for turning maker experiments into repeatable Futuroptimist episodes. It supports:

- drafting and validating per-video scripts;
- collecting YouTube metadata, transcripts, captions, and source references;
- indexing local media and per-video assets;
- rendering rough cuts and exportable editing timelines;
- maintaining Codex prompt docs and cross-repo automation; and
- exposing a local YouTube transcript CLI/API/MCP service for retrieval workflows.

For the full contributor workflow and roadmap, see [`INSTRUCTIONS.md`](../INSTRUCTIONS.md). For the production checklist, see [`RUNBOOK.md`](../RUNBOOK.md). AI-agent guidance lives in [`AGENTS.md`](../AGENTS.md), with creative context mirrored in [`llms.txt`](../llms.txt).

## Map of the repo

**Navigate in three hops:**

1. **Setup** – Follow [`INSTRUCTIONS.md`](../INSTRUCTIONS.md) for `uv` environment steps and contributor onboarding.
2. **Run** – Explore the [`Makefile`](../Makefile) targets for day-to-day automation; CLI helpers live in [`src/`](../src).
3. **Test** – Execute `make test` or `python -m pytest -q` to run the pytest suite.

| Category | Path / resource | Notes |
|----------|----------------|-------|
| Apps | _n/a_ | Entry points live in `src/` and `tools/`; there is no standalone product app in this repo. |
| Packages | [`src/`](../src) | Shared Python modules and CLI entry points for subtitles, scripts, metadata, assets, rendering, status updates, and reports. |
| Transcript service | [`tools/youtube_mcp/`](../tools/youtube_mcp) | CLI, FastAPI microservice, and MCP-compatible stdio server for YouTube transcripts. |
| Scripts | [`scripts/`](../scripts) | Operational helpers, prompt migrations, npm check wrappers, and credential-leak scans. |
| Video scripts | [`video_scripts/`](../video_scripts) | Per-video folders with `script.md`, `metadata.json`, and optional sources/assets/footage notes. |
| Subtitles | [`subtitles/`](../subtitles) | Downloaded `.srt` caption files populated by subtitle helpers. |
| Sources | [`sources/`](../sources) | Reference files fetched by source collection tooling. |
| Data | [`data/`](../data) | Lightweight generated/reference data for prompt docs and retrieval workflows. |
| Docs | [`docs/`](../docs) | Prompt docs, playbooks, this guide, and supporting documentation. |
| Schemas | [`schemas/`](../schemas) | JSON Schemas for video metadata, asset manifests, outage records, and related structured files. |
| Tests | [`tests/`](../tests) | Pytest suite mirroring production helpers. |
| Pipelines | [`outages/`](../outages) | Incident logs and schema-backed records for CI/workflow failures. |
| Infra | [`.github/workflows/`](../.github/workflows) | CI for lint, tests, docs, and scheduled Related Projects status updates. |

Prompt templates stay grouped under [`docs/prompts/codex/`](prompts/codex/) with an index in [`docs/README.md`](README.md). Video narration lives in [`video_scripts/`](../video_scripts), while local media and generated indexes are intentionally kept out of git when large or machine-specific.

## Setup and package notes

Python dependencies are managed with [`uv`](https://docs.astral.sh/uv/) and traditional requirement files. Treat this page as the stable map; the full onboarding flow, platform fallbacks, and current command details live in [`INSTRUCTIONS.md`](../INSTRUCTIONS.md).

For day-to-day orientation, the shortest path is usually:

```bash
make setup
make test
```

The Makefile handles common Windows/Unix path differences, and `make help` lists the current automation targets. Node is only used for repository hygiene scripts such as docs linting; npm scripts are defined in [`package.json`](../package.json).

## Automation and helper scripts

The repository aims to make video creation as repeatable as software delivery. Key helper workflows include:

- `python src/scaffold_videos.py` – create dated `video_scripts/YYYYMMDD_slug` folders from `video_ids.txt`.
- `python src/update_video_metadata.py` – refresh titles, publish dates, durations, thumbnails, descriptions, tags, and view counts via the YouTube Data API when `YOUTUBE_API_KEY` is available.
- `python src/update_transcript_links.py` – sync `transcript_file` paths and optionally fetch missing captions when API access is configured.
- `python src/collect_sources.py` – download reference files from configured source URL lists for citation/research workflows.
- `python src/newsletter_builder.py` or `make newsletter` – assemble Markdown digests of recent videos.
- `python src/fact_check_discussions.py` – export Futuroptimist GitHub Discussions fact-check threads to JSON.
- `python src/repo_status.py` – update the parseable `README.md` Related Projects dashboard with check-status emoji, timestamps, and direct failed-run links.

See [`INSTRUCTIONS.md`](../INSTRUCTIONS.md) for the complete workflow and current command examples.

## Script, metadata, subtitle, and asset workflow

Video folders under `video_scripts/` use `metadata.json` plus Markdown script files to keep drafts structured and retrievable.

- Scripts begin with a title heading, a YouTube ID blockquote, and a `## Script` section.
- Spoken lines use `[NARRATOR]:`; b-roll and graphics cues use `[VISUAL]:` directly after the dialogue they support.
- `metadata.json` files are validated against [`schemas/video_metadata.schema.json`](../schemas/video_metadata.schema.json).
- Optional `assets.json` manifests are validated against [`schemas/assets_manifest.schema.json`](../schemas/assets_manifest.schema.json).
- Optional `sources.txt` files list one URL per line for reference collection; downloaded materials are for citation/reference only.
- Optional `footage.md` files track archive clips, new footage, CGI, and generative AI shots.

Subtitle and transcript helpers:

- `make subtitles` / `python src/fetch_subtitles.py` downloads captions into `subtitles/`.
- `python src/srt_to_markdown.py` converts `.srt` captions into `[NARRATOR]` lines while stripping non-dialog cues and HTML noise.
- `python src/generate_scripts_from_subtitles.py` converts resolved subtitle files into `script.md` drafts.
- `python src/index_script_segments.py` exports narrator segments for retrieval.
- `python src/index_script_embeddings.py` hashes narrator segments into deterministic local test vectors.

Asset and render helpers:

- `python src/index_local_media.py` builds `footage_index.json` for local media under ignored `footage/` directories.
- `make index_assets` builds `assets_index.json` from per-video manifests.
- `python src/generate_assets_manifest.py --slug SLUG --overwrite` scaffolds `assets.json` from footage directories.
- `make convert_assets`, `make verify_assets`, and related conversion targets prepare footage for editing.
- `python src/render_video.py --slug SLUG` or `make render VIDEO=SLUG` builds rough-cut videos under `dist/`.
- `python src/create_otio_timeline.py --slug SLUG` emits portable OpenTimelineIO timelines for editing suites.

Generated indexes, large media, render outputs, and downloaded per-video reference files should stay out of commits unless the repo explicitly tracks them.

## YouTube Transcript MCP Service

[`tools/youtube_mcp/`](../tools/youtube_mcp) packages a transcript fetcher that powers a CLI, FastAPI microservice, and MCP-compatible stdio tool. It normalizes captions for retrieval, stores cached payloads in SQLite, and preserves provenance with timestamped cite URLs.

Entrypoints:

```bash
# HTTP service
python -m tools.youtube_mcp --host 127.0.0.1 --port 8765

# CLI transcript fetch
python -m tools.youtube_mcp.cli transcript --url https://youtu.be/VIDEOID

# MCP stdio server
python tools/youtube_mcp/mcp_server.py
```

Example HTTP call:

```bash
curl "http://127.0.0.1:8765/transcript?url=https://youtu.be/VIDEOID"
```

Policy notes:

- The service uses `youtube_transcript_api` and YouTube’s public oEmbed endpoint.
- It rejects private or unlisted videos when those signals are available.
- It does not scrape YouTube HTML or bypass authentication walls.

Caching and errors:

- Cache keys include video ID, language, and track type.
- Cached transcript payloads default to a 14-day TTL.
- Expired rows are purged automatically when accessed.
- Error codes such as `InvalidArgument`, `VideoUnavailable`, `NoCaptionsAvailable`, `PolicyRejected`, `RateLimited`, and `NetworkError` map to consistent HTTP responses and MCP error payloads.

## CI badges and workflows

Repo-level health is tracked by GitHub Actions rather than displayed at the top of the profile README:

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/futuroptimist/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/futuroptimist/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/futuroptimist/branch/main/graph/badge.svg)](https://app.codecov.io/gh/futuroptimist/futuroptimist/branch/main)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/futuroptimist/actions/workflows/03-docs.yml)

Primary workflows:

- `.github/workflows/01-lint-format.yml` – Python and JavaScript lint/format checks.
- `.github/workflows/02-tests.yml` – pytest with coverage on push and pull requests targeting `main`.
- `.github/workflows/03-docs.yml` – docs spellcheck and linkcheck.
- `.github/workflows/update-repo-status.yml` – scheduled hourly Related Projects status refresh.
- `.github/workflows/ci.yml` – focused YouTube MCP lint/test coverage for service-related paths.

Before committing, format code, run focused tests, and scan staged changes for credential leaks with:

```bash
git diff --cached | ./scripts/scan-secrets.py
```
