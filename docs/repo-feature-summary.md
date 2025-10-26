# Repo Feature Summary

This page tracks the Futuroptimist automation surfaces that are currently live and highlights
related projects that share the same tooling foundations.

## Futuroptimist automation snapshot
| Feature | Status | Notes |
| ---- | ------ | ----- |
| Prompt library | ✅ | Automation, CI fix, cleanup, spellcheck, and CAD prompts ship in-tree. |
| Testing guardrails | ✅ | Pytest keeps 100% coverage for subtitles, assets, metadata, prompts. |
| Credential scanning | ✅ | `scan-secrets.py` and the pre-commit wrapper block credential patterns. |
| Asset pipeline | ✅ | Conversion, verification, manifest generation, OTIO timeline export (`src/create_otio_timeline.py` + `tests/test_create_otio_timeline.py`), and funnel scripts keep footage reproducible. |
| Docs hygiene | ✅ | scripts/checks.sh runs docs-lint (see tests/test_checks_script.py). |
| Analytics dashboard | ✅ | Streamlit dashboard renders metrics captured by analytics_ingester (see tests/test_analytics_dashboard.py). |
| Upload packaging | ✅ | `src/prepare_youtube_upload.py` builds YouTube payloads with repo thumbnails (see `tests/test_prepare_youtube_upload.py`). |

## Companion projects quick scan
| Repo | Focus | Automation highlights |
| ---- | ----- | --------------------- |
| [token.place](https://github.com/futuroptimist/token.place) | Mesh | Shared prompts + AGENTS. |
| [gabriel](https://github.com/futuroptimist/gabriel) | Security | Shared prompts + scanning. |
| [axel](https://github.com/futuroptimist/axel) | Tracker | Codex automation triage. |
| [jobbot](https://github.com/futuroptimist/jobbot3000) | Copilot | Mirrors Futuroptimist prompts. |
