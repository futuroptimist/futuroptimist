# Futuroptimist Repository Guide

This document collects the full workflow for managing video scripts and metadata for the Futuroptimist YouTube channel. It mirrors the previous README content.

## Current State

1. **video_ids.txt** – list of the canonical YouTube IDs for each long-form video (no Shorts); lines starting with `#` are treated as comments.
2. **subtitles/** – English subtitle files (`.srt`) downloaded directly from YouTube. Use the helper script below to populate this folder.
3. **src/** – helper utilities and CLI tools.
4. **RUNBOOK.md** – living production checklist covering the end-to-end video workflow.
5. **llms.txt** and **AGENTS.md** – guidance files that help AI assistants understand the codebase structure, conventions and workflows.

> Video scripts live in `video_scripts/YYYYMMDD_slug/script.md` (auto-scaffolded). Idea files are collected in `ideas/` as checklists without date prefixes.

Schema guardrails: `tests/test_metadata_schema.py` now scans every
`video_scripts/**/metadata.json` and enforces `schemas/video_metadata.schema.json`
so malformed front-matter is caught during CI.

## Quick Start
```bash
# 1. Install dependencies (yt-dlp only for now)
uv pip install -r requirements.txt

# 2. Download available English subtitles into ./subtitles
python src/fetch_subtitles.py

# 3. Convert subtitles into Futuroptimist script format
python src/generate_scripts_from_subtitles.py

# 4. Run the full test suite (schema, naming, e2e)
make test
```
The script fetches **manual** subtitles only. Videos without manual captions are skipped. Files are saved as `subtitles/<videoid>.srt`.
If YouTube only offers WebVTT tracks, the fallback path converts them to `.srt` so downstream
tools stay compatible (see `tests/test_fetch_subtitles.py::test_download_subtitles_fallback_converts_vtt`).
Generate Markdown scripts from the downloaded captions with
`python src/generate_scripts_from_subtitles.py` (or `make scripts_from_subtitles`). The helper
creates `video_scripts/<slug>/script.md` files using the narration style covered by
`tests/test_generate_scripts_from_subtitles.py` so `[NARRATOR]` lines and timestamp comments match
the existing pipeline.

Turn finished captions into Futuroptimist scripts with:

```bash
python src/srt_to_markdown.py --slug YYYYMMDD_slug
```

The helper reads `video_scripts/YYYYMMDD_slug/metadata.json` to locate the YouTube ID,
loads `subtitles/<youtube_id>.srt`, and writes `script.md` with one `[NARRATOR]` line per
sentence (timestamps preserved in HTML comments). Pass `--no-overwrite` to keep an existing
script file in place. Regression coverage lives in
`tests/test_srt_to_markdown.py::test_generate_script_for_slug`.

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
make scripts_from_subtitles  # regenerate script.md files from subtitles
make clean      # remove the virtualenv and caches
make fmt       # format code with black & ruff
pre-commit install  # optional: run hooks (formatters) on commit
```

If Playwright-based tests complain about missing browsers, install them via:

```bash
npm run playwright:install
```

This wrapper calls `npx playwright install --with-deps` so CI and local runs stay aligned and
is covered by `tests/test_package_json.py::test_package_json_exposes_playwright_install_script`.

Lint prompt documentation tables (and catch stray trailing whitespace) with:

```bash
npm run docs-lint
```

The helper reuses `scripts/npm/run-checks.mjs` so both CI and local edits enforce the same
Markdown table shape in `docs/prompt-docs-summary.md` and whitespace hygiene in
`docs/prompts/codex/**/*.md`.

`make report_funnel` normalises selects entries so the resulting
`selections.json` stores repo-relative `footage/<slug>/converted/...` paths.
It also classifies selects as images, video, or audio (see
`tests/test_report_funnel.py::test_build_manifest_with_selects`). Entries that
attempt to escape the `converted/` directory (absolute paths or `..`
segments) are ignored so manifests can't reference outside assets (see
`tests/test_report_funnel.py::test_build_manifest_skips_outside_converted_entries`).
See `tests/test_report_funnel.py::test_build_manifest_normalizes_select_paths`
for coverage of this behaviour and
`tests/test_report_funnel.py::test_build_manifest_normalizes_slug_prefixed_paths`
for slug-prefixed selects that omit the `converted/` segment.

Some helper scripts require a GitHub token to access the GraphQL API. Export
`GH_TOKEN` (or `GITHUB_TOKEN`) with a personal access token that includes `repo`
and `read:org` scopes. You may also set `GH_TOKEN_FILE` or `GITHUB_TOKEN_FILE`
to point at a file containing the token. Paths in these variables may include
`~` or environment variables and will be expanded (see
`tests/test_collect_sources.py::test_resolve_source_urls_file_expands_env_and_user`
and
`tests/test_collect_sources.py::test_resolve_global_sources_dir_expands_env_and_user`).

Create new script folders from the IDs in `video_ids.txt`:

```bash
python src/scaffold_videos.py
```

This fetches titles and dates to generate `video_scripts/YYYYMMDD_slug` directories for drafting. Format code with `black .` and `ruff check --fix .` before committing.
If metadata can't be fetched (network issues or parsing errors) the script
logs the failure and continues so scaffolding never blocks your workflow.

If you need to revise a slug after scaffolding, run:

```bash
python src/rename_video_slug.py 20240101_old-slug --slug refreshed-slug
```

The helper renames the script folder, matching `footage/` directory, and
updates JSON metadata so asset manifests stay aligned (see
`tests/test_rename_video_slug.py`). Pass `--dry-run` to preview changes or
`--no-footage` to leave footage untouched.

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
belong to that script, optional label files (`labels.json`), capture date, tags,
and an optional `notes_file` pointer for shoot notes. Then run
`make index_assets` to generate a rich `assets_index.json` with per-asset path,
size, UTC mtime, linked script folder, tags, capture date, labels, and the
manifest's notes file so edit checklists stay discoverable (see
`tests/test_index_assets.py::test_build_index_with_labels`).

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
`--dry-run` to preview which files would change. Regression coverage in
`tests/test_enrich_metadata.py` now exercises the duration parser,
batched API fetches, dry-run output, and the real write path so
future edits stay regression-tested.

`tests/test_describe_images.py` covers the heuristic captioning so changes to
`src/describe_images.py` keep emitting meaningful alt-text summaries.

## Next Steps
* ~~Convert `.srt` caption timing into fully-fledged markdown scripts.~~ ✅ Use `make scripts_from_subtitles`.
* ~~Build a lightweight RAG pipeline that indexes past scripts for rapid outline generation of future videos.~~
  ✅ Run `python src/index_script_segments.py` to export `[NARRATOR]` lines into JSON chunks ready for embeddings
  (see `tests/test_index_script_segments.py`).

## 🌱 Roadmap / Flywheel Enhancements
The goal: turn this repo into a self-reinforcing engine that **accelerates Futuroptimist content velocity**.

| Phase | Feature | Impact |
|-------|---------|--------|
| 1️⃣  Plumbing | • **CI action now runs tests with coverage** on every push.<br>• Pre-commit hooks (black, ruff) | Confidence & code quality |
| 2️⃣  Metadata Automation | • YouTube Data API sync to enrich markdown front-matter (title, publish date, views, tags).<br>• Slug auto-generation + filename rename helper (`src/rename_video_slug.py`). | Less manual bookkeeping |
| 3️⃣  Script Intelligence | • SRT → Markdown converter that preserves timing blocks.<br>• Semantic chunker + embeddings (OpenAI / local) into `data/index` for RAG. | Opens door to AI-assisted new scripts |
| 4️⃣  Creative Toolkit | • Prompt library for hook/headline generation trained on past hits.<br>• Thumbnail text predictor (CTR estimation) using small vision model. | Higher audience retention |
| 5️⃣  Distribution Insights | • Analytics ingester (YouTube Analytics API) to pull watch-time & click-through data.<br>• Dashboards (Streamlit) to visualise topic performance vs retention. | Data-driven ideation |
| 6️⃣  Community | • GitHub Discussions integration for crowdsourced fact-checks.<br>• Scheduled newsletter builder that stitches new scripts + links. | Audience feedback loop |
| 7️⃣  Production Pipeline | • Adopt OpenTimelineIO as canonical timeline format.<br>• Asset manifest (audio, b-roll, gfx) auto-generated from `videos/<id>` folders.<br>• FFmpeg rendering scripts for rough-cut assembly and caption burn-in.<br>• CLI wrapper `make render VIDEO=xyz` → `dist/xyz.mp4`. | End-to-end reproducible builds |
| 8️⃣  Publish Orchestration | • YouTube Data API V3 upload endpoint (draft/private).<br>• Automatic thumbnail + metadata attach from repo files.<br>• Post-publish annotation back into metadata.json (video url, processing times). | One-command release |
| 9️⃣  Source Archival | • `collect_sources.py` downloads HTML/mp4 references from each `sources.txt` into `video_scripts/<slug>/sources/` folders and reads the root `source_urls.txt` into `/sources/` with a manifest (`sources.json`).<br>• Friendly `User-Agent`; see `tests/test_collect_sources.py::test_process_global_sources`. | Reliable citation & reproducibility |

*(Tick items as we progress!)*

---

© 2025 Futuroptimist – All rights reserved.
