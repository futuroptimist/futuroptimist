# Futuroptimist Repository Guide

This document collects the full workflow for managing video scripts and metadata for the Futuroptimist YouTube channel. It mirrors the previous README content.

## Current State

1. **video_ids.txt** – list of the canonical YouTube IDs for each long-form video (no Shorts).
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

## Development Workflow

Use the Makefile for common tasks:

```bash
make setup      # create .venv and install deps
make test       # run unit tests
make subtitles  # download captions listed in video_ids.txt
make clean      # remove the virtualenv and caches
make fmt       # format code with black & ruff
pre-commit install  # optional: run hooks (formatters + heatmap check) on commit
```

Some helper scripts require a GitHub token to access the GraphQL API. Export
`GH_TOKEN` (or `GITHUB_TOKEN`) with a personal access token that includes `repo`
and `read:org` scopes when generating heatmaps or fetching commit stats. You may
also set `GH_TOKEN_FILE` or `GITHUB_TOKEN_FILE` to point at a file containing
the token.

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
output directory if needed.

## Next Steps
* Automate enrichment of each video entry via the YouTube Data v3 API (publish date, title, duration, etc.).
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
