# Futuroptimist Repository Guide

This document collects the full workflow for managing video scripts and metadata for the Futuroptimist YouTube channel. It mirrors the previous README content.

## Current State

1. **video_ids.txt** – list of the canonical YouTube IDs for each long-form video (no Shorts); lines starting with `#` are treated as comments.
2. **subtitles/** – English subtitle files (`.srt`) downloaded directly from YouTube. Use the helper script below to populate this folder.
3. **src/** – helper utilities and CLI tools.
4. **RUNBOOK.md** – living production checklist covering the end-to-end video workflow.
5. **llms.txt** and **AGENTS.md** – guidance files that help AI assistants understand the codebase structure, conventions and workflows.

> Video scripts live in `video_scripts/YYYYMMDD_slug/script.md` (auto-scaffolded). Idea files are collected in `ideas/` as checklists without date prefixes.

## Quick Start
```bash
# 1. Install dependencies (yt-dlp only for now)
uv pip install -r requirements.txt

# 2. Download available English subtitles into ./subtitles
python src/fetch_subtitles.py

# 3. Run the full test suite (schema, naming, e2e)
make test
```
The script fetches **manual** subtitles only. Videos without manual captions are skipped. Files are saved as `subtitles/<videoid>.srt`.
If YouTube only offers WebVTT tracks, the fallback path converts them to `.srt` so downstream
tools stay compatible (see `tests/test_fetch_subtitles.py::test_download_subtitles_fallback_converts_vtt`).

## Development Workflow

Use the Makefile for common tasks:

```bash
make setup      # create .venv and install deps
make test       # run unit tests
make subtitles  # download captions listed in video_ids.txt
make index_footage  # build simple footage_index.json (paths, mtime, size)
make index_assets   # build rich assets_index.json from per-video assets.json
make describe_images  # scan images and write heuristic captions to image_descriptions.md
make convert_assets   # convert incompatible originals/ into converted/ via ffmpeg
make convert_all      # convert images+videos for all slugs (or SLUG=YYYYMMDD_slug)
make verify_assets    # verify converted assets match originals
make report_funnel SLUG=<slug> [SELECTS=path]  # write selections.json for the slug
make process SLUG=<slug> [SELECTS=path]        # one-command: convert+verify+report
make clean      # remove the virtualenv and caches
make fmt       # format code with black & ruff
pre-commit install  # optional: run hooks (formatters) on commit
```

Use the companion npm scripts to keep prompt docs tidy:

```bash
npm run lint         # flag trailing whitespace in docs/prompts/codex/*.md
npm run format:check # ensure package.json stays two-space formatted with a trailing newline
npm run test:ci      # verify docs/prompt-docs-summary.md renders a two-column table
```

Some helper scripts require a GitHub token to access the GraphQL API. Export
`GH_TOKEN` (or `GITHUB_TOKEN`) with a personal access token that includes `repo`
and `read:org` scopes. You may also set `GH_TOKEN_FILE` or `GITHUB_TOKEN_FILE`
to point at a file containing the token. Paths in these variables may include
`~` or environment variables and will be expanded.

Create new script folders from the IDs in `video_ids.txt`:

```bash
python src/scaffold_videos.py
```

This fetches titles and dates to generate `video_scripts/YYYYMMDD_slug` directories for drafting. Format code with `black .` and `ruff check --fix .` before committing.
If metadata can't be fetched (network issues or parsing errors) the script
logs the failure and continues so scaffolding never blocks your workflow.

Large media assets should live in a local `footage/` directory.
Use `python src/index_local_media.py` to build `footage_index.json`
so you can quickly locate clips while editing. Each entry includes
the file path, modification time in UTC, and size in bytes, sorted
deterministically by timestamp then path. The script creates the
output directory if needed and skips the index file itself when rerun
inside the footage directory. Pass `--exclude PATH` (repeatable) to
omit specific files or folders from the index.

Metadata enrichment: run `python src/update_video_metadata.py`
(or `make update_metadata`) to refresh video titles, publish dates,
durations, descriptions, and keyword tags using YouTube Data API v3.
Provide `YOUTUBE_API_KEY` in the environment. The tool only rewrites
files when values change and is covered by
`tests/test_update_video_metadata.py`.

Per‑video manifests: add `video_scripts/<folder>/assets.json` conforming to
`schemas/assets_manifest.schema.json` to declare which `footage/` directories
belong to that script, optional label files (`labels.json`), capture date, and
tags. Then run `make index_assets` to generate a rich `assets_index.json` with
per-asset path, size, UTC mtime, linked script folder, tags, capture date, and
labels.

Asset conversion (Premiere compatibility): run `make convert_assets` to scan
`footage/<slug>/originals/` for formats like HEIC/HEIF, DNG, WEBP and convert
them to Premiere-friendly JPG/PNG under `footage/<slug>/converted/` with the
same relative structure. HEIC/HEIF/DNG stills are exported as high-quality
`.jpg` files, while WEBP graphics stay `.png`. Originals are preserved. Use
`python src/convert_assets.py --dry-run` to preview and `--force` to overwrite
existing outputs. See `tests/test_convert_assets.py` for regression coverage of
the extension mapping.

Run `python src/enrich_metadata.py` to pull each video's title, publish date,
and duration directly from the YouTube Data v3 API when `metadata.json`
contains a `youtube_id`. Export `YOUTUBE_API_KEY` before running; add
`--dry-run` to preview which files would change. The behaviour is covered by
`tests/test_enrich_metadata.py` so future edits stay regression-tested.

`tests/test_describe_images.py` covers the heuristic captioning so changes to
`src/describe_images.py` keep emitting meaningful alt-text summaries.

## Next Steps
* Convert `.srt` caption timing into fully-fledged markdown scripts.
* Build a lightweight RAG pipeline that indexes past scripts for rapid outline generation of future videos.

## 🌱 Roadmap / Flywheel Enhancements
The goal: turn this repo into a self-reinforcing engine that **accelerates Futuroptimist content velocity**.

| Phase | Feature | Impact |
|-------|---------|--------|
| 1️⃣  Plumbing | • **CI action now runs tests with coverage** on every push.<br>• Pre-commit hooks (black, ruff) | Confidence & code quality |
| 2️⃣  Metadata Automation | • YouTube Data API sync to enrich markdown front-matter (title, publish date, views, tags).<br>• Slug auto-generation + filename rename helper. | Less manual bookkeeping |
| 3️⃣  Script Intelligence | • SRT → Markdown converter that preserves timing blocks.<br>• Semantic chunker + embeddings (OpenAI / local) into `data/index` for RAG. | Opens door to AI-assisted new scripts |
| 4️⃣  Creative Toolkit | • Prompt library for hook/headline generation trained on past hits.<br>• Thumbnail text predictor (CTR estimation) using small vision model. | Higher audience retention |
| 5️⃣  Distribution Insights | • Analytics ingester (YouTube Analytics API) to pull watch-time & click-through data.<br>• Dashboards (Streamlit) to visualise topic performance vs retention. | Data-driven ideation |
| 6️⃣  Community | • GitHub Discussions integration for crowdsourced fact-checks.<br>• Scheduled newsletter builder that stitches new scripts + links. | Audience feedback loop |
| 7️⃣  Production Pipeline | • Adopt OpenTimelineIO as canonical timeline format.<br>• Asset manifest (audio, b-roll, gfx) auto-generated from `videos/<id>` folders.<br>• FFmpeg rendering scripts for rough-cut assembly and caption burn-in.<br>• CLI wrapper `make render VIDEO=xyz` → `dist/xyz.mp4`. | End-to-end reproducible builds |
| 8️⃣  Publish Orchestration | • YouTube Data API V3 upload endpoint (draft/private).<br>• Automatic thumbnail + metadata attach from repo files.<br>• Post-publish annotation back into metadata.json (video url, processing times). | One-command release |
| 9️⃣  Source Archival | • `collect_sources.py` downloads HTML/mp4 references from `sources.txt` into `sources/` subfolders with a friendly `User-Agent`.<br>• `sources.json` maps URLs to filenames for easy citation. | Reliable citation & reproducibility |

*(Tick items as we progress!)*

---

© 2025 Futuroptimist – All rights reserved.
