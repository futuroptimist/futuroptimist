# Prompt Saturation Rubric

Use this checklist to decide when to pause new implementation prompt variants and instead run
`docs/prompts/codex/polish.md` for consolidation.

## When to pivot

- [ ] Recent `implement.md` runs deliver overlapping edits or target the same files within 48 hours.
- [ ] Review cycles spend more time resolving merge conflicts than introducing new behavior.
- [ ] Coverage or doc updates dominate diffs, signalling features have stabilized.
- [ ] Stakeholders request guidance, release notes, or onboarding clarity more than features.

When two or more boxes are checked, favor the polish workflow before authoring more
`implement.md` variants. Capture notes about the trigger and resulting clean-up tasks below.

## Collision log

- [ ] Date + PR link:
- [ ] Collision summary:
- [ ] Follow-up polish actions queued:
