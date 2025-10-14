# Futuroptimist Documentation Index

## Prompt docs (Codex)

All Codex-ready prompts live under `docs/prompts/codex/`:

- [automation.md](prompts/codex/automation.md) — Standard automation workflow kickoff.
- [cad.md](prompts/codex/cad.md) — Guidance for CAD-focused build prompts.
- [ci-fix.md](prompts/codex/ci-fix.md) — Recover from CI failures with targeted fixes.
- [cleanup.md](prompts/codex/cleanup.md) — Streamline and tidy existing changes.
- [fuzzing.md](prompts/codex/fuzzing.md) — Drive fuzzing experiments and document findings.
- [implement.md](prompts/codex/implement.md) — Primary implementation work prompt.
- [physics.md](prompts/codex/physics.md) — Physics explainer and validation helper.
- [polish.md](prompts/codex/polish.md) — Evergreen polish and structure prompt.
- [propagate.md](prompts/codex/propagate.md) — Share updates across sibling repos.
- [spellcheck.md](prompts/codex/spellcheck.md) — Run focused spelling and style passes.
- [video-script-ideas.md](prompts/codex/video-script-ideas.md) — Brainstorm future episode outlines.

For a cross-repo inventory, see [prompt-docs-summary.md](prompt-docs-summary.md).

## Prompt doc maintenance

Use the migration helper to keep prompt docs consolidated and consistently named:

```sh
./scripts/migrate-prompt-docs.sh
```

The script is idempotent, so re-running it after edits is safe.

## Prompt strategy tracker

- [prompt-saturation-rubric.md](prompt-saturation-rubric.md) — Checklist for deciding when to
  pivot from implementation prompts toward polish-focused passes as variants converge.
