# Video Production Runbook (v0.1)

This document is a living checklist covering the **Futuroptimist** long-form video pipeline.

> Check off each task (`[x]`) as you move from _idea_ to _publish_.

---

## 1. Ideation & Research

- [ ] Brainstorm topic ideas in the `ideas/` directory (each idea stored as its own Markdown file).
- [ ] Validate relevance using keyword research / trend tools.
- [ ] Draft one-sentence value proposition.

## 2. Script Writing

- [ ] Create `<DATE>_<N>_<slug>.md` in `scripts/` with front-matter:
  ```yaml
  ---
  youtube_id:
  title:
  publish_target:
  status: draft
  ---
  ```
- [ ] Outline (hook, context, body, payoff).
- [ ] Write full narration.
- [ ] Peer / AI review for clarity and pacing.

## 3. Pre-Production

- [ ] Prepare A-roll shot list.
- [ ] Collect B-roll references / stock.
- [ ] Finalise visual assets (charts, slides, props).
- [ ] Book location & gear.

## 4. Production

- [ ] Film A-roll.
- [ ] Capture B-roll.
- [ ] Backup footage to cloud/NAS.

### 🔍 Verification Gate
- [ ] Run `make test` – all unit & schema checks must pass before moving to post-production.

## 5. Post-Production

- [ ] Rough cut (sync audio, remove dead air).
- [ ] Insert B-roll & graphics.
- [ ] Colour grade & audio mix.
- [ ] Generate captions.
- [ ] Export final 4K master.

## 6. Distribution

- [ ] Write SEO-optimised title & description.
- [ ] Design thumbnail (A/B variants).
- [ ] Upload to YouTube (schedule).
- [ ] Publish transcript to repo.

## 7. Promotion

- [ ] Share on BlueSky / Threads / Mastodon.
- [ ] Post vertical clip on Shorts / Reels / TikTok.
- [ ] Add to newsletter.

## 8. Post-Launch Review

- [ ] Collect engagement metrics after 48h / 7d / 30d.
- [ ] Debrief wins & improvements.

---

### Legend

| Status | Meaning |
| ------ | ------- |
| draft  | early work-in-progress |
| ready  | script locked & queued |
| filming| actively shooting |
| edit   | in post-production |
| live   | published on channel |

---

_Last updated: 2025-06-09_
