# Futuroptimist 👋

*Building open-source tools so anyone can invent, automate & explore.*

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/futuroptimist/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/futuroptimist/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/futuroptimist/branch/main/graph/badge.svg)](https://app.codecov.io/gh/futuroptimist/futuroptimist/branch/main)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/futuroptimist/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/futuroptimist/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/futuroptimist)](LICENSE)

Hi, I'm Futuroptimist. This repository hosts scripts and metadata for my
[YouTube channel](https://www.youtube.com/@futuroptimist).
If you're looking for the full project details, see
[INSTRUCTIONS.md](INSTRUCTIONS.md). We manage Python dependencies with
[uv](https://docs.astral.sh/uv/); check the instructions for setup steps.
Guidelines for AI tools live in [AGENTS.md](AGENTS.md).
The canonical Codex prompt for automated contributions is in
[docs/prompts/codex/automation.md](docs/prompts/codex/automation.md).
The automated tests run via GitHub Actions on each push and pull request and currently
reach **100%** coverage.

## Map of the repo

**Navigate in three hops:**

1. **Setup** – Follow [INSTRUCTIONS.md](INSTRUCTIONS.md) for `uv` environment steps and
   contributor onboarding.
2. **Run** – Explore the [Makefile](Makefile) targets for day-to-day automation; CLI helpers
   live in [`src/`](src).
3. **Test** – Execute `make test` (documented in `INSTRUCTIONS.md`) to run the full pytest
   suite with coverage.

| Category | Path / resource | Notes |
|----------|----------------|-------|
| Apps | _n/a_ | Entry points live in `src/`; no standalone services yet. |
| Packages | [`src/`](src) | Shared Python modules and CLI entry points. |
| Scripts | [`scripts/`](scripts) | Operational helpers (e.g., prompt migrations, scans). |
| Data | [`data/prompt-docs/`](data/prompt-docs) | Lightweight reference lists synced with docs. |
| Docs | [`docs/`](docs) | Prompts, playbooks, and supporting guides. |
| Tests | [`tests/`](tests) | Pytest suite mirroring production helpers. |
| Pipelines | [`outages/`](outages) | Incident logs and schema describing stability. |
| Infra | [`.github/workflows/`](.github/workflows) | CI for lint, tests, docs, status updates. |

Prompt templates stay grouped under
[`docs/prompts/codex/`](docs/prompts/codex) with an index in
[`docs/README.md`](docs/README.md). Video narration lives in [`video_scripts/`](video_scripts),
and multimedia assets are catalogued via the Makefile targets above.

## YouTube Transcript MCP Service

The repository now ships a small, self-contained transcript service designed for MCP tools,
local microservice use, and CLI workflows. The service normalizes captions fetched from
`youtube_transcript_api`, chunks them into RAG-ready windows with provenance links, and caches
responses on disk for 14 days by default.

**Run modes**

- HTTP: `python -m tools.youtube_mcp --host 127.0.0.1 --port 8765`
- MCP (stdio): `python tools/youtube_mcp/mcp_server.py`
- CLI: `python -m tools.youtube_mcp.cli transcript --url https://www.youtube.com/watch?v=VIDEOID`

**HTTP endpoints**

- `GET /health` – service health
- `GET /transcript` – query params: `url`, optional `lang`, `prefer_auto`
- `GET /tracks` – available caption tracks (manual first)
- `GET /metadata` – lightweight metadata (title/channel when available)

**CLI usage**

```bash
python -m tools.youtube_mcp.cli transcript --url https://youtu.be/VIDEOID
python -m tools.youtube_mcp.cli tracks --url VIDEOID
python -m tools.youtube_mcp.cli metadata --url VIDEOID
```

**Caching & settings**

| Environment variable | Default | Purpose |
|----------------------|---------|---------|
| `YTMCP_CACHE_DIR` | `.ytmcp_cache` | Cache directory (sqlite backing) |
| `YTMCP_CACHE_TTL_DAYS` | `14` | Cache TTL in days |
| `YTMCP_ALLOW_AUTO` | `true` | Permit auto-generated captions when manual tracks missing |
| `YTMCP_REJECT_PRIVATE_OR_UNLISTED` | `true` | Reject private or unlisted videos |
| `YTMCP_HTTP_HOST` | `127.0.0.1` | Default HTTP bind host |
| `YTMCP_HTTP_PORT` | `8765` | Default HTTP port |

**Error codes**

| Code | Meaning |
|------|---------|
| `InvalidArgument` | Input validation failed |
| `VideoUnavailable` | Video cannot be accessed |
| `NoCaptionsAvailable` | No captions provided by YouTube |
| `PolicyRejected` | Private/unlisted or disallowed content |
| `NetworkError` | Upstream network failure |
| `RateLimited` | Rate limiting encountered |

Policy reminder: the service respects YouTube ToS by using official caption endpoints, avoiding
HTML scraping, and refusing private or unlisted videos when configured (default `true`). Metadata
requests rely on the oEmbed endpoint only and do not attempt authenticated or prohibited access.

> **uv cheat sheet**: `uv sync` installs dependencies from `requirements.txt`,
> `uv run pytest` mirrors `make test`, and `uvx <tool>` launches one-off binaries without
> polluting the virtual environment.

## Related Projects
_Last updated: 2025-11-06 06:02 UTC; checks hourly_
Status icons: ✅ latest run succeeded, ❌ failed or cancelled, ❓ no completed runs.
The unknown state is enforced by
`tests/test_repo_status.py::test_fetch_repo_status_no_runs_returns_unknown`, ensuring repositories
without completed workflows render `❓` instead of failing the dashboard.

- ✅ **[futuroptimist](https://github.com/futuroptimist/futuroptimist)** – central hub for
  reproducible scripts, data pipelines, and tests that turn maker experiments into
  polished YouTube episodes
- ✅ **[token.place](https://token.place)** – secure peer-to-peer generative AI network that
  lets volunteers share idle compute through ephemeral, encrypted tokens—no sign-ups
  required ([repo](https://github.com/futuroptimist/token.place))
- ✅ **[DSPACE](https://democratized.space)** @v3 – retro-futurist idle sim where quests teach
  real-world hobbies with NPC guides; offline-first so your space-base thrives without a
  signal ([repo](https://github.com/democratizedspace/dspace/tree/v3))
- ✅ **[flywheel](https://github.com/futuroptimist/flywheel)** – GitHub template that bundles
  lint, tests, docs, and release automation with LLM agents so solo builders ship like a
  team
- ✅ **[gabriel](https://github.com/futuroptimist/gabriel)** – privacy-first "guardian angel"
  LLM that learns your environment and delivers local, actionable security coaching
- ✅ **[f2clipboard](https://github.com/futuroptimist/f2clipboard)** – CLI that parses Codex
  task pages, grabs failing GitHub logs, and pipes concise reports straight to your
  clipboard to speed debugging
- ✅ **[axel](https://github.com/futuroptimist/axel)** – LLM-powered quest tracker that
  analyzes your repos and curates next steps to keep side projects moving
- ✅ **[sigma](https://github.com/futuroptimist/sigma)** – open-source ESP32 AI pin with
  push-to-talk voice control, running speech-to-text, LLM, and TTS in a 3D-printed case so
  commands stay local
- ✅ **[gitshelves](https://github.com/futuroptimist/gitshelves)** – turns your GitHub
  contributions into stackable 3D-printable blocks that fit 42 mm Gridfinity baseplates,
  turning commit history into shelf art
- ✅ **[wove](https://github.com/futuroptimist/wove)** – open toolkit for learning to knit and
  crochet while evolving toward robotic looms, bridging CAD workflows with textiles
- ❌ **[sugarkube](https://github.com/futuroptimist/sugarkube)** – solar-powered k3s platform
  and cube art installation for Raspberry Pi clusters, making off-grid edge Kubernetes
  plug-and-play
- ✅ **[pr-reaper](https://github.com/futuroptimist/pr-reaper)** – GitHub workflow that closes
  your own stale pull requests in bulk with a safe dry-run
- ✅ **[danielsmith.io](https://github.com/futuroptimist/danielsmith.io)** – Vite + Three.js
  playground for an orthographic, keyboard-navigable portfolio scene
- ✅ **[jobbot3000](https://github.com/futuroptimist/jobbot3000)** – self-hosted job search copilot
  sharing the same automation scaffold as this repo

## Values

We aim for a positive-sum, empathetic community that shares knowledge openly.

---

Licensed under the [MIT License](LICENSE).
