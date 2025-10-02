---
title: 'Codex Prompt Propagation Prompt'
slug: 'codex-propagate'
---

# Codex Prompt Propagation Prompt
Type: evergreen

Use this prompt to ask Codex to seed missing `docs/prompts/codex/*.md` files across repositories listed in
[`docs/prompt-docs-summary.md`](../../prompt-docs-summary.md).

**Human set-up steps:**

1. Ensure `dict/prompt-doc-repos.txt` lists the target repositories:

   ```text
   flywheel
   futuroptimist
   jobbot3000
   pr-reaper
   danielsmith.io
   ```

   Then regenerate [`docs/prompt-docs-summary.md`](../../prompt-docs-summary.md):

  ```bash
  python scripts/update_prompt_docs_summary.py \
    --repos-from dict/prompt-doc-repos.txt \
    --out docs/prompt-docs-summary.md
  ```
   The updater now fetches each repo's automation prompt and linked guides from the list in
   `dict/prompt-doc-repos.txt`, so the summary highlights cross-repo gaps automatically (see
   `tests/test_update_prompt_docs_summary.py`).
2. Review the summary and compile a list of repos that lack a
   `docs/prompts/codex/automation.md` baseline.
3. Paste that list (one repo per line) at the top of your ChatGPT message.
4. Add two blank lines, then copy the block below and send it.

```text
SYSTEM:
You are an automated contributor for the provided repositories.

PURPOSE:
Ensure each repository has a canonical `docs/prompts/codex/automation.md` file so future agents have
guidance.

CONTEXT:
- For each repo in the list, check for existing `docs/prompts/codex/*.md` files.
- If none exist, create `docs/prompts/codex/automation.md` based on the version in
  `futuroptimist/futuroptimist`.
- Follow the repository's `AGENTS.md`, style guides, and commit conventions.
- Run the repository's lint and test suite before committing:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `npm run lint` and `npm run test:ci` if a `package.json` is present
  - `python -m flywheel.fit` if the module is available
  - `bash scripts/checks.sh`

REQUEST:
1. Clone the repository and add the prompt doc.
2. Include a short README update linking to the new doc.
3. Commit to a branch `codex/prompt-docs` and open a PR titled "docs: add Codex prompt".
4. Return the pull request URL.

OUTPUT:
A list of pull request links, one per repository.
```

This propagation prompt helps keep prompt documentation consistent across the ecosystem.

## Upgrade Prompt
Type: evergreen

Use this prompt to refine the propagation instructions.

```text
SYSTEM:
You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Keep this propagation prompt accurate for seeding prompt docs.

 CONTEXT:
 - Follow `AGENTS.md` and `README.md`.
 - Ensure `pre-commit run --all-files` and `pytest -q` pass.
 - If a `package.json` exists, run `npm run lint` and `npm run test:ci`.
 - If the `flywheel` module is available, run `python -m flywheel.fit`.
 - Run `bash scripts/checks.sh`.
 - Regenerate `docs/prompt-docs-summary.md` with
   `python scripts/update_prompt_docs_summary.py --repos-from \
  dict/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.

REQUEST:
1. Review this file for outdated repository lists or steps.
2. Update content and regenerate the summary.
3. Run the checks above.

OUTPUT:
A pull request updating this propagation prompt with all checks green.
```
