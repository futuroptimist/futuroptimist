---
title: 'Codex CI-Failure Fix Prompt'
slug: 'codex-ci-fix'
---

# OpenAI Codex CI-Failure Fix Prompt
Type: evergreen

Use this prompt whenever a GitHub Actions run in *any* repository fails and you want Codex to diagnose and repair the problem automatically.
**Human set-up steps (do these *before* switching ChatGPT into “Code” mode):**

1. Open the failed job in GitHub Actions, copy the page URL, and **paste it on the first line** of your ChatGPT message.
2. Press <kbd>Enter</kbd> twice so that exactly **two blank lines** follow the URL.
3. Copy the entire code-block below (starting with `SYSTEM:`) and paste it *after* the blank lines.
4. Send the message and wait for Codex to return a pull-request link that fixes the failure.

```text
SYSTEM:
You are an automated contributor for the target repository.

PURPOSE:
Diagnose a failed GitHub Actions run and produce a fix.

CONTEXT:
- Follow `AGENTS.md` and `README.md`.
- Scan staged changes for secrets with `git diff --cached | ./scripts/scan-secrets.py`.
- Ensure the following pass:
  - `pre-commit run --all-files`
  - `pytest -q`
  - `npm ci` (if `package.json` exists)
  - `npm run lint` (if `package.json` exists)
  - `npm run test:ci` (if `package.json` exists)
  - `python -m flywheel.fit` (if installed)
  - `bash scripts/checks.sh`
- Regenerate `docs/prompt-docs-summary.md` with:
  `python scripts/update_prompt_docs_summary.py --repos-from dict/prompt-doc-repos.txt \
  --out docs/prompt-docs-summary.md`.

REQUEST:
1. Read the failure logs and locate the first real error.
2. Explain (in the pull-request body) *why* the failure occurred.
3. Commit the necessary code, configuration, or documentation changes.
4. Record the incident in `outages/YYYY-MM-DD-<slug>.json` using `outages/schema.json`,
   and write a matching `outages/YYYY-MM-DD-<slug>.md` postmortem.
5. Push to a branch named `codex/ci-fix/<short-description>`.
6. Open a pull request that – once merged – makes the default branch CI-green.
7. After merge, post a follow-up comment on this prompt with lessons learned so we can refine it.

OUTPUT:
A GitHub pull request URL. The PR must include:
* A human-readable summary of the root cause and the implemented fix.
* Evidence that **all** checks are now passing (`✔️`).
* Links to any new or updated tests.
Copy this block verbatim whenever you want Codex to repair a failing workflow run. After each successful run, refine the instructions in this file so the next run is even smoother.
After opening the pull request, add a postmortem under `outages/`.
Name it `YYYY-MM-DD-short-title.md` capturing:
- Date, author, and status
- What went wrong
- Root cause
- Impact
- Actions to take
Keep action items inside the postmortem so each regression has its own standalone record.
Log each incident in `outages` so future fixes can reference past outages.
```

### Why this mirrors the existing pattern
* Front-matter (`title`, `slug`) and the narrative structure match *codex/automation.md* in **DSPACE** so that docs render consistently.
* Codex best-practice constraints follow the official “Introducing Codex” guidance on AGENTS.md-driven projects.
* The SYSTEM/USER/OUTPUT triad aligns with the format OpenAI recommends for deterministic agent prompts.

---

## 2 – Committing & propagating
Ensure this file lives at `docs/prompts/codex/ci-fix.md`.

Regenerate the prompt summary:

```bash
python scripts/update_prompt_docs_summary.py \
  --repos-from dict/prompt-doc-repos.txt \
  --out docs/prompt-docs-summary.md
```

Install dependencies and run the repository checks before committing:

```bash
uv venv
uv pip install -r requirements.txt
pre-commit run --all-files
pytest -q
bash scripts/checks.sh
git diff --cached | ./scripts/scan-secrets.py
```

Ensure `dict/prompt-doc-repos.txt` matches `docs/repo_list.txt` so downstream repos stay
connected.

Push and open a PR in flywheel. Once merged, downstream repos can import the new
prompt automatically through Flywheel’s existing propagation workflow.

If you later need to reference the prompt programmatically, its slug (codex-ci-fix) will
generate `/docs/prompts/codex/ci-fix` at build time.

## 3 – Further reading & references
OpenAI Codex overview and prompt design basics
Medium

How Codex consumes AGENTS.md files for repo-specific context
GitHub

Community discussion on AGENTS.md placement
OpenAI Community

Example of an AGENTS.md template (independent guide)
Agents.md Guide for OpenAI Codex

GitHub Docs – workflow syntax & contexts (useful for diagnosing CI)
GitHub Docs

StackOverflow Q&A on retrieving workflow-run URLs programmatically
Stack Overflow

GitHub Community thread on exposing run URLs inside jobs
GitHub

Markdown Guide – extended table syntax
CommonMark Discussion

Escaping pipes in Markdown tables
Stack Overflow

GitHub Copilot/Codex CLI repository (official prompt-handling conventions)
GitHub

Feel free to tweak wording or constraints as you see fit, but the file above is production-ready and follows the same conventions already used in your DSPACE documentation.

## Upgrade Prompt
Type: evergreen

Use this prompt to refine the CI-failure fix instructions.

```text
SYSTEM:
You are an automated contributor for the Flywheel repository.

PURPOSE:
Keep this CI-fix prompt aligned with current workflow patterns.

  CONTEXT:
  - Follow `AGENTS.md` and `README.md`.
  - Inspect `.github/workflows/` and mirror CI steps locally.
  - Ensure `pre-commit run --all-files`, `pytest -q`, and
    `bash scripts/checks.sh` pass.
  - If `package.json` exists, `scripts/checks.sh` also runs
    `npm run lint` and `npm run test:ci`.
  - Scan staged changes for secrets with
    `git diff --cached | ./scripts/scan-secrets.py`.
  - Regenerate `docs/prompt-docs-summary.md` with
    `python scripts/update_prompt_docs_summary.py --repos-from \
    dict/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.
  - Keep `dict/prompt-doc-repos.txt` in sync with `docs/repo_list.txt`. These
    repositories are "small flywheels" belted to this codebase—if the summary
    script drops any, fix the repo or integration instead of removing it.

REQUEST:
1. Audit this document for outdated guidance or missing steps.
2. Update wording and regenerate the summary.
3. Run the checks above.

OUTPUT:
A pull request updating this CI-fix prompt with all checks green.
```
