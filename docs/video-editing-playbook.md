## Futuroptimist Video Editing Playbook

Purpose: A fast, repeatable path from long selects to a tight 3–5 minute video that feels purposeful, paced, and clear. Use this as a checklist when cutting.

### 0) Define the job of the video
- Audience: makers, educators, open-source enthusiasts
- Outcome: one clear idea delivered cleanly; 1–2 takeaways; 1 call-to-action
- Through‑line: a single sentence that everything must serve

### 1) Gather and Prep
- Import only from `footage/<slug>/converted/`
- Run repo helpers as needed:
  - `make verify_assets`
  - `make describe_images`
  - `make convert_all SLUG=<slug>`
- Create bins: Dialogue, B‑roll, Music, SFX, Graphics

### 2) Selects Pass (speed pass)
- Skim at 2x; mark I/O and keep only decisive moments
- Save to a "Selects" sequence; label gems (⭐) and cutaways (↔)

### 3) Radio Edit (story first)
- Cut the narrative only (no b‑roll yet)
- Keep the 5–7 strongest beats:
  1. Hook (first 5–10s)
  2. Context (why this matters)
  3. Promise (what you’ll learn/see)
  4. Body (3–4 proof beats or demos)
  5. Reframe (surprising insight)
  6. Payoff (result/demo/outcome)
  7. CTA (subscribe/next step/source files)
- Aim for ~220–260 wpm pacing; remove filler and tangents

### 4) Picture Pass (b‑roll + visuals)
- Cover every cut with motion-first b‑roll (hands, builds, faces, graphs)
- Prefer variety: wide → medium → detail, left/right alternation
- Use J/L cuts to keep audio flowing across picture changes
- Add 2–3 on-screen labels max; consistent style

### 5) Tighten Timing
- Kill dead air; trim breaths; keep snappiness between thoughts
- Shorten or remove any shot that doesn’t add new info or emotion
- Reserve speed ramps for emphasis (≤2 in a 4‑min cut)

### 6) Color & Sound (90/10)
- Color: basic exposure/white balance; contrast; gentle saturation
- Dialogue: target ~‑14 LUFS integrated, peaks ≤‑6 dB
- Music: low bed (‑24 to ‑18 LUFS), duck ‑6 to ‑10 dB under voice
- SFX: restraint; 1–2 tasteful whooshes/clicks if they clarify motion

### 7) Titles & Thumbnails
- Title formula: problem → promise → specificity (avoid clickbait)
- Thumbnail: one idea, 3–5 words; readable at 120px; avoid clutter
- Consistency beats novelty; update templates rather than re‑invent
- Evaluate overlay text with
  `python src/thumbnail_text_predictor.py --text "HOOK" thumbnail.png`
  (regression in `tests/test_thumbnail_text_predictor.py`).

### 8) Review Loops
- Watch once at 1x; fix pacing
- Listen eyes‑closed; fix audio clarity and rhythm
- External check: ask “what’s the point?” after 30s and at the end

### 9) Publish Checklist (preview)
- Verify credits and sources (APA in script folder)
- Confirm asset rights for any third‑party footage
  - Ensure `metadata.json` has publish date, tags, thumbnail path, and a
    positive `view_count`
    (_enforced by `tests/test_metadata_schema.py::test_live_metadata_includes_publish_details`_).
    `python src/update_video_metadata.py` now also records the highest-resolution
    thumbnail URL from YouTube and the latest view counts (see
    `tests/test_update_video_metadata.py::test_updates_metadata_from_api`).
    Live metadata entries are additionally checked to keep HTTPS YouTube
    thumbnail URLs via
    `tests/test_metadata_schema.py::test_live_metadata_thumbnails_are_urls`.

### Anti‑Patterns to Avoid
- Visual repetition without new information
- Over-explaining; use visuals instead
- Excess text on screen; keep it minimal
- Unmotivated camera moves/transitions/sound effects

### Useful Repo Commands
```bash
make convert_all SLUG=<slug>
make verify_assets
make describe_images  # refresh heuristic image captions
make index_assets
```

Keep this playbook evolving—PRs welcome with techniques that improve clarity, pacing, or repeatability.
