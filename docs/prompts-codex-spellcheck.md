---
title: 'Codex Spellcheck Prompt'
slug: 'prompts-codex-spellcheck'
---

# Codex Spellcheck Prompt

Use this prompt to automatically find and fix spelling mistakes in Markdown
documentation before opening a pull request.

```text
SYSTEM:
You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Keep Markdown documentation free of spelling errors.

CONTEXT:
- Check all Markdown files using `pyspelling -c spellcheck.yaml`.
- Add unknown but legitimate words to `.wordlist.txt`.
- Follow `AGENTS.md` and `README.md`.
- Ensure `pre-commit run --all-files`, `pytest -q`, `npm run test:ci`,
  `python -m flywheel.fit`, and `bash scripts/checks.sh` pass.
- Regenerate `docs/prompt-docs-summary.md` with
  `python scripts/update_prompt_docs_summary.py --repos-from dict/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.

REQUEST:
1. Run the spellcheck command and inspect the results.
2. Correct misspellings or update `.wordlist.txt` as needed.
3. Re-run `pyspelling` until it reports no errors.
4. Commit the changes with a concise message and open a pull request.

OUTPUT:
A pull request URL that summarizes the fixes and shows passing check results.
```

Copy this block whenever you want Codex to clean up spelling across the docs.

## Upgrade Prompt
Type: evergreen

Use this prompt to refine the spellcheck instructions.

```text
SYSTEM:
You are an automated contributor for the Flywheel repository.

PURPOSE:
Keep this spellcheck prompt accurate as tooling evolves.

CONTEXT:
- Follow `AGENTS.md` and `README.md`.
- Ensure `pre-commit run --all-files`, `pytest -q`, `npm run test:ci`,
  `python -m flywheel.fit`, and `bash scripts/checks.sh` pass.
- Regenerate `docs/prompt-docs-summary.md` with
  `python scripts/update_prompt_docs_summary.py --repos-from \
  dict/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.

REQUEST:
1. Review this file for outdated commands or paths.
2. Update content and regenerate the summary.
3. Run the checks above.

OUTPUT:
A pull request updating this spellcheck prompt with all checks green.
```
