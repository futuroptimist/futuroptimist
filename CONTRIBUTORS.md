# Contributors Guide

✨ **Thank you for your interest in helping Futuroptimist!** This project thrives on community ideas, bug-fixes and improvements from humans and AI agents alike.

## Ways to Contribute
1. **Ideas & Roadmap** – Propose new video topics or tooling features by adding Markdown files in `ideas/` (see ideas/README.md).
2. **Code** – Bug-fixes, tests, CI scripts, render pipeline, data-ingestion, etc.
3. **Documentation** – Improve README, runbook, or in-code docstrings.
4. **Creative Assets** – Solarpunk graphics, music cues, timeline templates.

## Pull Request workflow
1. **Fork** the repo & create a feature branch.
2. **Run locally**:
   ```bash
   make setup    # or ./setup.ps1
   make test
   ```
3. Keep PRs focused (one logical change).
4. If you add code, add matching **unit tests**.
5. Ensure `make test` passes (unit + schema + naming conventions) and `pre-commit` hooks (if installed) are green.
6. Open PR ➜ fill template (description, rationale, screenshots).

## Coding standards
- Python 3.11+, black formatted, ruff-linted (coming via CI).
- Prefer pure-python & cross-platform solutions.
- No large binaries in git (link via release or separate repo).

## License
All contributions are licensed under the repository's MIT license (see LICENSE).

## Code of Conduct
Be kind & constructive; no harassment, hate speech, or spam. This content is intended for a global, eco-positive audience.

---
**Core maintainer:** Daniel (@Futuroptimist). Feel free to @-mention for reviews or questions! 