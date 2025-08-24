# Contributing

✨ **Thank you for your interest in helping Futuroptimist!** This project thrives on ideas and improvements from humans and AI agents alike.

## Quick Start

Run `make setup` (or `./setup.ps1` on Windows) then `make test`.
If the Makefile fails on your platform, create a virtual environment manually:

```bash
python3 -m venv .venv && uv pip install -r requirements.txt
```

## Ways to Contribute
1. **Ideas & Roadmap** – Add markdown files in `ideas/` for new video topics or tooling features.
2. **Code** – Bug fixes, tests, CI scripts, render pipeline, data-ingestion, etc.
3. **Documentation** – Improve README, runbook, or docstrings.
4. **Creative Assets** – Solarpunk graphics, music cues, timeline templates.

## Pull Request Workflow
1. **Fork** the repo and create a feature branch.
2. **Run locally**:
   ```bash
   make setup  # or ./setup.ps1
   make test
   ```
3. Keep PRs focused (one logical change). If you add code, also add **unit tests** and run `make subtitles` when relevant.
4. Ensure `make test` passes and any pre-commit hooks are green.
5. Open the PR and fill in the template with description, rationale and screenshots if helpful.

## Coding standards
- Python 3.11+, formatted with `black` and checked with `ruff`.
- Prefer pure-python and cross-platform solutions.
- No large binaries committed to Git – link via releases or a separate repo.

## License

All contributions are licensed under the repository's MIT license (see `LICENSE`).

## Code of Conduct

Be kind and constructive. Harassment, hate speech or spam will not be tolerated.

---
**Core maintainer:** Daniel (@Futuroptimist). Feel free to @-mention for reviews or questions!
