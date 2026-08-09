# Repo Feature Summary

This page tracks the Futuroptimist automation surfaces that are currently live. For related
projects, see the automatically refreshed
[Related Projects](https://github.com/futuroptimist/futuroptimist#related-projects) section of
the README instead of maintaining a second, hand-written list here.

## Futuroptimist automation snapshot
| Feature | Status | Notes |
| ---- | ------ | ----- |
| Prompt library | ✅ | Automation, CI fix, cleanup, spellcheck, and CAD prompts ship in-tree. |
| Testing guardrails | ✅ | Pytest keeps 100% coverage for subtitles, assets, metadata, prompts. |
| Credential scanning | ✅ | `scan-secrets.py` and the pre-commit wrapper block credential patterns. |
| Asset pipeline | ✅ | Conversion, verification, manifest generation, OTIO timeline export (`src/create_otio_timeline.py` + `tests/test_create_otio_timeline.py`), and funnel scripts keep footage reproducible. |
| Docs hygiene | ✅ | scripts/checks.sh runs docs-lint (see tests/test_checks_script.py). |
| Analytics dashboard | ✅ | Streamlit dashboard renders metrics captured by analytics_ingester (see tests/test_analytics_dashboard.py). |
| Upload packaging | ✅ | `src/prepare_youtube_upload.py` builds payloads and `src/upload_to_youtube.py` ships draft uploads (see `tests/test_prepare_youtube_upload.py`, `tests/test_upload_to_youtube.py`). |
