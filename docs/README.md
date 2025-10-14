# Futuroptimist Documentation Index

## Prompt docs (Codex)

All Codex-ready prompts live under `docs/prompts/codex/`, and filenames already omit the
redundant words “prompt” and “codex.” Quick reference:

| File | Purpose |
|------|---------|
| [automation.md](prompts/codex/automation.md) | Standard automation workflow kickoff. |
| [cad.md](prompts/codex/cad.md) | Guidance for CAD-focused build prompts. |
| [ci-fix.md](prompts/codex/ci-fix.md) | Recover from CI failures with targeted fixes. |
| [cleanup.md](prompts/codex/cleanup.md) | Streamline and tidy existing changes. |
| [fuzzing.md](prompts/codex/fuzzing.md) | Drive fuzzing experiments and document findings. |
| [implement.md](prompts/codex/implement.md) | Primary implementation work prompt. |
| [physics.md](prompts/codex/physics.md) | Physics explainer and validation helper. |
| [polish.md](prompts/codex/polish.md) | Evergreen polish and structure prompt. |
| [propagate.md](prompts/codex/propagate.md) | Share updates across sibling repos. |
| [spellcheck.md](prompts/codex/spellcheck.md) | Focused spelling and style passes. |
| [video-script-ideas.md](prompts/codex/video-script-ideas.md) | Outline future episodes. |

For a cross-repo inventory, see [prompt-docs-summary.md](prompt-docs-summary.md). If new prompt
guides are added, place them alongside these canonical names or introduce missing counterparts
such as `agents.md` or `playbook.md`.

## Prompt doc maintenance

Use the migration helper to keep prompt docs consolidated, renamed, and idempotent:

```sh
./scripts/migrate-prompt-docs.sh
```

The script moves any markdown file in `docs/` whose path contains “prompt” or “codex” into the
canonical folder, normalises the filename (for example `cad-prompt.md` → `cad.md`), and prints
`Prompt docs already consolidated at …` when re-runs have no work to do.

## Prompt strategy tracker

- [prompt-saturation-rubric.md](prompt-saturation-rubric.md) — Checklist with collision
  checkboxes for deciding when to pivot from implementation prompts toward polish-focused passes.
