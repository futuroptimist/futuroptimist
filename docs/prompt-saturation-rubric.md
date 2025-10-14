# Prompt Saturation Rubric

Use this checklist to decide when to pause new implementation prompt variants and instead run
`docs/prompts/codex/polish.md` for consolidation.

## Saturation signals

Tick at least two boxes before queuing a polish-focused pass:

- [ ] Three consecutive `implement.md` runs touched the same module or file family.
- [ ] Review cycles spend more time resolving merge conflicts than introducing new behavior.
- [ ] Coverage, doc, or comment-only updates dominate diffs across the last three variants.
- [ ] Stakeholders request guidance, release notes, or onboarding clarity more than features.
- [ ] Infra or CI changes repeat across multiple variants (rerun migrations, bump identical deps).

When two or more boxes are checked, favor the polish workflow before authoring more
`implement.md` variants. Capture notes about the trigger and resulting clean-up tasks below.

## Collision log template

Copy this block per collision cluster to keep the saturation state visible:

- [ ] Date observed:
- [ ] Overlapping PRs / branches:
- [ ] Files or directories repeatedly in conflict:
- [ ] Follow-up polish owner:
- [ ] Linked polish PR or doc updates:
- [ ] Retrospective notes:
