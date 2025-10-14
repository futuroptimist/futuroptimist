---
title: 'Codex Implement Prompt'
slug: 'codex-implement'
---

# Codex Implement Prompt
Type: evergreen

Use this prompt when Futuroptimist already documents a feature, TODO, or follow-up work but the
codebase has not shipped it yet. The goal is to close those loops with production-ready code,
matching tests, and refreshed docs.

## When to use it

- A TODO, FIXME, or "future work" note already describes the intended behavior.
- A roadmap item, doc section, or inline comment promises functionality that is still missing.
- Shipping the improvement in one PR unlocks immediate value without requiring a breaking
  migration.

## Prompt block

```prompt
SYSTEM:
You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Deliver the documented-but-unimplemented features that Futuroptimist already promises.

USAGE NOTES:
- Prompt name: `prompt-implement`.
- Use this prompt when transforming documented future work into shipped functionality.
- Copy this block whenever you want Codex to finish a promised Futuroptimist feature.

CONTEXT:
- Follow [`AGENTS.md`](../../../AGENTS.md) and [`README.md`](../../../README.md) for repo norms.
- Review [`docs/prompt-docs-summary.md`](../../prompt-docs-summary.md) so related prompt docs stay
  discoverable.
- Inspect [`llms.txt`](../../../llms.txt) for tone and project framing before editing narrative
  files.
- Check `.github/workflows/` to mirror CI; run the same commands locally:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `npm run test:ci`
  - `bash scripts/checks.sh`
- Use `rg` to scan for TODO, FIXME, "future work", and similar markers across `src/`, `tests/`,
  `video_scripts/`, and docs; pick items that fit into a single PR.
- Add targeted automated tests. Start with a failing test, then cover happy paths and regressions.
- Keep changes composable. Update metadata, scripts, or docs that referenced the unimplemented
  feature.
- Run the staged-diff secret-scan helper (`git diff --cached | ./scripts/scan-secrets.py`) before
  committing.

REQUEST:
1. Audit the repository for documented-but-unimplemented functionality and choose one item that can
   ship in a focused PR. Summarize why it is actionable now.
2. Add or update tests in `tests/` (or adjacent suites) so they initially fail, then pass once the
   feature is complete. Maintain Futuroptimist's testing style.
3. Implement the feature with the smallest viable change. Remove or refresh stale TODOs and comments
   that promised the behavior.
4. Update related docs (e.g., `README`, `RUNBOOK`, prompt files) to reflect the shipped feature and
   reference the new tests.
5. Run the commands above (`pre-commit`, `pytest -q`, `npm run test:ci`,
   `bash scripts/checks.sh`, staged-diff secret-scan helper). Resolve failures and capture outcomes
   for the PR body.

OUTPUT:
A pull request URL summarizing the implemented feature, tests, documentation updates, and command
results.
```

## Upgrade Prompt
Type: evergreen

Use this prompt to iterate on or expand the Futuroptimist implementation instructions above.

```upgrade
SYSTEM:
You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Improve `docs/prompts/codex/implement.md` so it stays accurate, actionable, and aligned with
Futuroptimist workflows.

USAGE NOTES:
- Use this prompt when refining the implement prompt itself.

CONTEXT:
- Follow [`AGENTS.md`](../../../AGENTS.md), [`README.md`](../../../README.md), and
  [`llms.txt`](../../../llms.txt).
- Review `.github/workflows/` to anticipate CI checks. Run:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `npm run test:ci`
  - `bash scripts/checks.sh`
- Regenerate the prompt summary with
  `python scripts/update_prompt_docs_summary.py --repos-from data/prompt-docs/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.
- Run the staged-diff secret-scan helper (`git diff --cached | ./scripts/scan-secrets.py`) before
  committing.

REQUEST:
1. Review `docs/prompts/codex/implement.md` for outdated instructions, links, or scope.
2. Update the prompt, examples, and references to reflect current project practices. Ensure all
   linked files exist.
3. Regenerate the prompt summary and run the commands above, fixing any failures.

OUTPUT:
A pull request updating `docs/prompts/codex/implement.md` with all checks green.
```
