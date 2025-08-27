---
title: 'Codex Fuzzing Prompt'
slug: 'codex-fuzzing'
---

# OpenAI Codex Fuzzing Prompt
Type: evergreen

Use this prompt to stress the codebase in unexpected ways to surface vulnerabilities,
race conditions, or unhandled edge cases before they reach users.

**Human setup steps:**
1. Paste the path of the module or component to fuzz (use `./` for the whole repo).
2. Add two blank lines.
3. Copy the block below and send it in ChatGPT Code mode.

```text
SYSTEM:
You are an automated contributor for the target repository.

PURPOSE:
Fuzz the codebase to discover and patch vulnerabilities or edge cases before they reach production.

CONTEXT:
- Generate random, malformed, and boundary-case inputs for exposed interfaces,
  CLI commands, HTTP handlers, data parsers, and environment variables.
- Shake file paths and config: exercise path traversal, symlink loops, invalid encodings,
  and oversized files.
- Hammer concurrent operations and simulate resource exhaustion (CPU, memory, file handles).
- Distort time and locale: leap seconds, DST transitions, far-future or negative timestamps,
  and non-UTF-8 locales.
- Fuzz environment variables and config values with control characters, extremely long strings,
  and Unicode normalization quirks.
- Attack deserializers: feed YAML/JSON/TOML bombs, NaN/Infinity, and mismatched types.
- Stress compression and archive handlers with zip/tar bombs, truncated archives,
  and zip-slip paths.
- Simulate flaky networks: packet loss, reordering, half-open sockets, and truncated responses.
- Fuzz cross-platform file I/O: reserved device names, deep or Unicode paths,
  and case-insensitive collisions.
- Probe subprocess boundaries with unexpected signals (SIGINT/SIGPIPE) and slow or partial streams.
- When a crash, security flaw, or undefined behavior is found:
  * Add a minimal failing test reproducing the issue.
  * Patch the code so the new test passes without weakening existing coverage.
  * Note any security impact and mitigation steps.
- Record each incident in `outages/YYYY-MM-DD-incident.json` using `outages/schema.json`.
- Create a companion postmortem in `docs/pms/YYYY-MM-DD-short-title.md`
  summarizing the root cause and fix.
- Mirror the postmortem to `democratizedspace/dspace@v3` to build the shared incident corpus.

REQUEST:
1. Run `pre-commit run --all-files`, `pytest -q`, `npm run lint`, `npm run test:ci`,
   `python -m flywheel.fit`, and `bash scripts/checks.sh`.
2. Commit the failing test, the fix, and documentation updates.
3. Push to a branch named `codex/fuzzing/short-desc` and open a pull request.
4. Link the postmortem and dspace entry in the PR description.

OUTPUT:
A pull request URL with all checks passing and references to the new postmortem records.
```

Copy this block whenever you want Codex to fuzz-test the repository. Refine the
prompt as new failure modes are discovered.

## Upgrade Prompt
Type: evergreen

Use this prompt to refine the fuzzing instructions.

```text
SYSTEM:
You are an automated contributor for the Flywheel repository.

PURPOSE:
Keep this fuzzing prompt current with emerging edge cases.

CONTEXT:
- Follow `AGENTS.md` and `README.md`.
- Ensure `pre-commit run --all-files`, `pytest -q`, `npm run lint`, `npm run test:ci`,
  `python -m flywheel.fit`, and `bash scripts/checks.sh` pass.
- Regenerate `docs/prompt-docs-summary.md` with
  `python scripts/update_prompt_docs_summary.py --repos-from \
  dict/prompt-doc-repos.txt --out docs/prompt-docs-summary.md`.

REQUEST:
1. Review this file for outdated or missing fuzzing guidance.
2. Update content and regenerate the summary.
3. Run the checks above.

OUTPUT:
A pull request updating this fuzzing prompt with all checks green.
```
