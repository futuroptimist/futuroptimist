---
title: 'Codex Prompt Cleanup'
slug: 'codex-cleanup'
---

# Obsolete Prompt Cleanup
Type: evergreen

Use this prompt to remove one-off prompts already implemented and clean up lingering references.

```text
SYSTEM: You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Maintain prompt hygiene by deleting fulfilled one-off prompts and clearing outdated references.

CONTEXT:
- Scan `docs/prompts/codex/` for `Type: one-off` prompts whose features now exist in the codebase.
- Delete each obsolete prompt file or section and remove any lingering references.
- Regenerate `docs/prompt-docs-summary.md` with:
  `python scripts/update_prompt_docs_summary.py --repos-from dict/prompt-doc-repos.txt \
  --out docs/prompt-docs-summary.md`.
  This command now pulls the automation prompt (and linked guides) for every repository listed
  in `dict/prompt-doc-repos.txt`, so cross-repo prompt inventories stay current. Regression
  coverage lives in `tests/test_update_prompt_docs_summary.py`.
- Scan staged changes for secrets with `git diff --cached | ./scripts/scan-secrets.py`.
- Run checks:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `npm ci` (if `package.json` exists)
  - `npm run lint` (if `package.json` exists)
  - `npm run test:ci` (if `package.json` exists)
  - `bash scripts/checks.sh`

REQUEST:
1. Locate an obsolete prompt.
2. Remove it and refresh references such as `docs/prompt-docs-summary.md`.
3. Run all required checks before committing.

OUTPUT:
A pull request that deletes outdated prompts and cleans up related references.
```

## Upgrade Prompt
Type: evergreen

Use this prompt to refine the cleanup instructions.

```text
SYSTEM:
You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Keep this cleanup prompt effective for removing obsolete items.

CONTEXT:
- Follow `AGENTS.md` and `README.md`.
- Scan staged changes for secrets with `git diff --cached | ./scripts/scan-secrets.py`.
- Ensure the following pass:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `npm ci` (if `package.json` exists)
  - `npm run lint` (if `package.json` exists)
  - `npm run test:ci` (if `package.json` exists)
  - `bash scripts/checks.sh`
- Regenerate `docs/prompt-docs-summary.md` with:
  `python scripts/update_prompt_docs_summary.py --repos-from dict/prompt-doc-repos.txt \
  --out docs/prompt-docs-summary.md`.

REQUEST:
1. Review this file for outdated steps or unclear language.
2. Update content and regenerate the summary.
3. Run the checks above.

OUTPUT:
A pull request that improves this cleanup prompt with all checks green.
```
