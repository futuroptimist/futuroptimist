# AGENTS.md

> Guidance for AI tools and contributors working in the Futuroptimist repository. The project blends maker builds with forward‑looking tech essays in a solarpunk style. This file implements the [AgentsMD](https://agentsmd.net/) specification and mirrors the repo details provided in [`llms.txt`](llms.txt).

Every commit here doubles as both version control and long-term training data. Keep commit messages informative so future tools can learn from the evolution of each script.
Keep `llms.txt` synchronized with changes to this guide so LLMs stay current.

The main `README.md` is intentionally minimal to maintain a clean GitHub profile.
Avoid adding setup or asset instructions there; link to INSTRUCTIONS instead.

## Key Information

- **Primary Topic**: Open-source maker builds and tech storytelling
- **Secondary Topics**: 3‑D printing, space exploration, sustainability and lightweight ML tools
- **Audience**: Makers, educators and open-source enthusiasts
- **Repository URL**: <https://github.com/futuroptimist/futuroptimist>
- **Spec References**: [AgentsMD](https://agentsmd.net/) and [llms.txt](https://llmstxt.org/)

## Repo Layout

| Path | Purpose |
|------|---------|
| `/src/` | Helper utilities and CLI tools. |
| `/video_scripts/` | Per-video folders (`YYYYMMDD_slug/`) containing `script.md`, `metadata.json`, and optional `sources.txt` or `footage.md`. Run `scaffold_videos.py` to fetch titles/dates and create folders from `video_ids.txt`. |
| `/ideas/` | Checklist-style idea files – raw, WIP content. |
| `/schemas/` | JSON-Schemas (e.g. `video_metadata.schema.json`). |
| `/tests/` | Pytest suites; keep parity with production code. |
| `/Makefile` & `setup.ps1` | Developer automation (venv, tests, subtitles, render). |
| `/llms.txt` | Complementary file containing creative context & tone. |
| `/subtitles/` | Downloaded `.srt` caption files populated by `fetch_subtitles.py`. |
| `/src/srt_to_markdown.py` | Convert `.srt` captions into Futuroptimist script format (handles italics and emoji) |
| `/src/generate_heatmap.py` | Create a 3‑D lines-of-code heatmap with light/dark SVGs |
| `/sources/` | Reference files fetched via `collect_sources.py`. |
| `video_ids.txt` | Canonical list of YouTube IDs referenced by helper scripts. |
| `video_scripts/<id>/sources/` | Downloaded reference files for that video generated by `collect_sources.py` (gitignored). |
| `INSTRUCTIONS.md` | Extended setup steps and roadmap. |

## Coding Conventions

* Python 3.11+, black formatting & ruff lint. A `.pre-commit-config.yaml` runs these along with `generate_heatmap.py`.
* Run `black .` and `ruff check --fix .` (or `make fmt`) before committing. Hooks fire automatically if you run `pre-commit install`.
* One logical change per PR; always include/extend tests.
* Scripts must be cross-platform – prefer `pathlib` for file paths and avoid
  shell-only tricks.
* Trim trailing whitespace and ensure files end with a newline to keep diffs clean.

## Script Format

Video scripts (`video_scripts/YYYYMMDD_slug/script.md`) combine narration and stage
directions. Use `[NARRATOR]:` for spoken lines and `[VISUAL]:` for b-roll or
graphics cues. Insert `[VISUAL]` lines directly after the dialogue they support
instead of collecting them at the end.
- Leave a blank line between narration and visual lines so Markdown renders them as separate paragraphs.
- When importing transcripts from `.srt` files, strip prefix markers like `- [Narrator]` and split sentences into individual `[NARRATOR]` lines for clarity.
- Break long transcript sentences at punctuation boundaries so each `[NARRATOR]` line contains a single, complete thought.
- Start each script with a level-one heading containing the video title,
  followed by a blockquote referencing the YouTube ID and a `## Script` section header.
- Each script folder must include a `metadata.json` file conforming to `schemas/video_metadata.schema.json`. Optional fields like `slug`, `thumbnail`, `transcript_file`, and `summary` enrich automation but aren't required.
- Each script folder may include a `sources.txt` file with one URL per line. Any downloaded articles or clips are for reference only—check usage rights and cite sources in **APA style** rather than redistributing content.
- Each script folder may also contain a `footage.md` checklist to track B-roll or CGI shots to gather. Note existing archive vs new footage, and flag generative AI segments so they don't look like "AI slop".
- Large photos or video files belong in a local `footage/` folder (ignored by git). Run `python src/index_local_media.py` whenever assets change to rebuild `footage_index.json` for quick lookup during editing.
- Run `python src/update_transcript_links.py` to sync `transcript_file` paths; with `YOUTUBE_API_KEY` set it also fetches missing captions via YouTube Data API.

## Testing & CI

Run `make subtitles` and `python src/collect_sources.py` to download captions and reference files when needed.

The repository includes a simple GitHub Actions workflow (`.github/workflows/02-tests.yml`)
that installs dependencies and runs the full test suite with coverage on every
push or pull request.

### Data & Schemas
- [source_urls.txt](source_urls.txt): URLs consumed by `collect_sources.py`.

```bash
make setup   # venv + deps (or ./setup.ps1)
make test    # runs `pytest -q`
# To check coverage locally:
pytest --cov=./src --cov=./tests
```
The Makefile auto-detects Windows vs Unix paths so these commands should work cross-platform.
If `make setup` fails on your platform, run `python3 -m venv .venv && uv pip install -r requirements.txt` then `pytest -q`.
If `make test` errors about `.venv/Scripts/python`, use `PATH=.venv/bin:$PATH pytest -q` instead.
If `yt-dlp` cannot be located during tests, prefix your command with `PATH=.venv/bin:$PATH` so the venv's executables are discoverable.

CI runs `pytest --cov=./src --cov=./tests` on every push and pull request targeting `main`. In a future phase it may also run `make subtitles` to verify caption downloads.
Aim to keep coverage at **100%** so the Codecov badge stays green.

When adding CLI entrypoint tests, stub out any network requests (e.g. patch
`urllib.request.urlopen`) so tests remain deterministic even if external sites
are unreachable.

## Vision & Workflow

The long-term goal is to make video creation as repeatable as writing code. Every finalized script lives under `video_scripts/` alongside its metadata and will later feed a retrieval system (or even fine-tuning) so AI tools can draft new outlines in the Futuroptimist voice. Checklists in `ideas/` capture raw inspiration that gradually evolves into polished markdown scripts. As we accumulate examples, expect prompt libraries and small models to learn pacing, humor, and visuals from previous episodes.

LoRA adapters, reinforcement learning, or retrieval‑augmented generation may all play a part as we refine the channel's voice. Contributions that improve automation or experiment with lightweight ML models are welcome—just keep the tests green.

## Render & Publish (Future-Phase)

When Phase 7 hits (see the roadmap in INSTRUCTIONS.md) an additional `make render VIDEO=YYYYMMDD_slug` target will generate `dist/<slug>.mp4`. Subsequent automation will call YouTube Data API for upload.

## Contribution Quick-Start

1. Fork & branch.
2. `make setup` then `make test`.
3. `python src/scaffold_videos.py` to pull metadata and create dated script folders from `video_ids.txt` (commit new folders).
4. Optionally run `make subtitles` to verify caption downloads.
5. Add or update code **and** matching tests.
6. Commit with descriptive message; open PR.
7. `make clean` removes the virtual env & caches if you need a fresh start.

## Additional Resources (File List)

### Documentation
- [README](README.md): concise because it doubles as the GitHub profile. Do **not** include Makefile commands, footage instructions, or other setup details here—they belong in INSTRUCTIONS or RUNBOOK.
- Avoid detailed how-tos like subtitle downloading; store them in other docs.
- [INSTRUCTIONS](INSTRUCTIONS.md): full workflow and roadmap.
- [RUNBOOK](RUNBOOK.md): production checklist.
- [Ideas guide](ideas/README.md): idea-file schema.

### Schemas
- [Video Metadata Schema](schemas/video_metadata.schema.json): strict JSON schema for `metadata.json`.

Tests under `tests/` cover folder naming (`test_folder_names.py`), schema validation (`test_metadata_schema.py`) and the helper scripts. Extend them when adding new features.

### Optional
- [Contributing guide](CONTRIBUTING.md): PR etiquette and code style details.
- For cross-project synergy, see the README's **Other Projects** links or explore the [axel](https://github.com/futuroptimist/axel), [gitshelves](https://github.com/futuroptimist/gitshelves), [wove](https://github.com/futuroptimist/wove), and [sugarkube](https://github.com/futuroptimist/sugarkube) repos.

---
*For creative context, tone, and thematic constraints refer to [`llms.txt`](llms.txt).* 

