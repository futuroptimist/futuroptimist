# Futuroptimist Repository Guide

This document collects the full workflow for managing video scripts and metadata for the Futuroptimist YouTube channel. It mirrors the previous README content.

## Current State

1. **video_ids.txt** – list of the canonical YouTube IDs for each long-form video (no Shorts).
2. **subtitles/** – English subtitle files (`.srt`) downloaded directly from YouTube. Use the helper script below to populate this folder.
3. **scripts/** – helper utilities such as subtitle fetchers.
4. **RUNBOOK.md** – living production checklist covering the end-to-end video workflow.
5. **llms.txt** and **AGENTS.md** – guidance files that help AI assistants understand the codebase structure, conventions and workflows.

> Video scripts live in `scripts/YYYYMMDD_slug/script.md` (auto-scaffolded). Idea files are collected in `ideas/` as checklists without date prefixes.

## Quick Start
```bash
# 1. Install dependencies (yt-dlp only for now)
pip install -r requirements.txt

# 2. Download available English subtitles into ./subtitles
python scripts/fetch_subtitles.py

# 3. Run the full test suite (schema, naming, e2e)
make test
```
The script pulls **manual** subtitles when present, falling back to **auto-generated** captions as needed. Files are saved as `subtitles/<videoid>.srt`.

## Next Steps
* Automate enrichment of each video entry via the YouTube Data v3 API (publish date, title, duration, etc.).
* Convert `.srt` caption timing into fully-fledged markdown scripts.
* Build a lightweight RAG pipeline that indexes past scripts for rapid outline generation of future videos.

## 🌱 Roadmap / Flywheel Enhancements
The goal: turn this repo into a self-reinforcing engine that **accelerates Futuroptimist content velocity**.

| Phase | Feature | Impact |
|-------|---------|--------|
| 1️⃣  Plumbing | • CI action that runs tests + subtitle fetcher on every push.<br>• Pre-commit hooks (black, ruff) | Confidence & code quality |
| 2️⃣  Metadata Automation | • YouTube Data API sync to enrich markdown front-matter (title, publish date, views, tags).<br>• Slug auto-generation + filename rename helper. | Less manual bookkeeping |
| 3️⃣  Script Intelligence | • SRT → Markdown converter that preserves timing blocks.<br>• Semantic chunker + embeddings (OpenAI / local) into `data/index` for RAG. | Opens door to AI-assisted new scripts |
| 4️⃣  Creative Toolkit | • Prompt library for hook/headline generation trained on past hits.<br>• Thumbnail text predictor (CTR estimation) using small vision model. | Higher audience retention |
| 5️⃣  Distribution Insights | • Analytics ingester (YouTube Analytics API) to pull watch-time & click-through data.<br>• Dashboards (Streamlit) to visualise topic performance vs retention. | Data-driven ideation |
| 6️⃣  Community | • GitHub Discussions integration for crowdsourced fact-checks.<br>• Scheduled newsletter builder that stitches new scripts + links. | Audience feedback loop |
| 7️⃣  Production Pipeline | • Adopt OpenTimelineIO as canonical timeline format.<br>• Asset manifest (audio, b-roll, gfx) auto-generated from `videos/<id>` folders.<br>• FFmpeg rendering scripts for rough-cut assembly and caption burn-in.<br>• CLI wrapper `make render VIDEO=xyz` → `dist/xyz.mp4`. | End-to-end reproducible builds |
| 8️⃣  Publish Orchestration | • YouTube Data API V3 upload endpoint (draft/private).<br>• Automatic thumbnail + metadata attach from repo files.<br>• Post-publish annotation back into metadata.json (video url, processing times). | One-command release |

*(Tick items as we progress!)*

---

© 2025 Futuroptimist – All rights reserved.
