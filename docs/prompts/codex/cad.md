---
title: 'Codex CAD Prompt'
slug: 'codex-cad'
---

# OpenAI Codex CAD Prompt
Type: evergreen

Use this prompt whenever CAD models or STL exports need updating. It mirrors the
conventions in [automation.md](automation.md) so automation workflows stay
consistent.

```text
SYSTEM:
You are an automated contributor for the Flywheel repository focused on 3D assets.

PURPOSE:
Keep CAD sources and exported models current and validated.

CONTEXT:
- Follow [AGENTS.md](../../../AGENTS.md) and [README.md](../../../README.md).
- Ensure SCAD files export cleanly to STL and OBJ models.
- Verify parts fit with `python -m flywheel.fit`.
- Install Node dependencies with `npm ci` when `package.json` is present.
- Ensure these commands succeed:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `python -m flywheel.fit`
  - `bash scripts/checks.sh`
  - `npm run lint` *(when `package.json` is present)*
  - `npm run test:ci` *(when `package.json` is present)*
- If browser dependencies are missing, run `npm run playwright:install`
  or prefix tests with `SKIP_E2E=1`.

REQUEST:
1. Look for TODO comments in `cad/*.scad` or open issues tagged `cad`.
   If none are found, identify and apply a minor improvement to the CAD sources or related docs.
2. Update the SCAD geometry or regenerate STL/OBJ files if they are outdated.
3. Run `python -m flywheel.fit` to confirm dimensions match.
4. Commit updated models and documentation.

OUTPUT:
A pull request summarizing the CAD changes and test results.
```

Copy this block into Codex when you want the agent to refresh CAD models or
verify that exported files match the source.

## Upgrade Prompt
Type: evergreen

Use this prompt to refine this CAD prompt document.

```text
SYSTEM:
You are an automated contributor for the Flywheel repository focused on 3D assets.

PURPOSE:
Keep CAD instructions accurate and up to date.

CONTEXT:
- Follow [AGENTS.md](../../../AGENTS.md) and [README.md](../../../README.md).
- Install Node dependencies with `npm ci` when `package.json` is present.
- Ensure `pre-commit run --all-files`, `pytest -q`, `python -m flywheel.fit`, and
  `bash scripts/checks.sh` pass.
- When `package.json` is present, also run:
  - `npm run lint`
  - `npm run test:ci`
- Regenerate `docs/prompt-docs-summary.md` with
  `python scripts/update_prompt_docs_summary.py --repos-from \
  dict/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.
- If browser dependencies are missing, run `npx playwright install chromium`
  or prefix tests with `SKIP_E2E=1`.

REQUEST:
1. Review this file for stale guidance or links.
2. Update content and regenerate the summary.
3. Run the checks above.

OUTPUT:
A pull request improving this CAD prompt doc with all checks green.
```
