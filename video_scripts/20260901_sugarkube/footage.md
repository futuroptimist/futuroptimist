# Sugarkube footage master index

This is the canonical production index for [the script](script.md). Detailed, nonduplicated asset checklists live in [original B-roll](production/broll.md), [third-party stock](production/stock.md), and [manual graphics](production/graphics.md).

## Media policy

This production permits original footage, original screen recordings, manually produced graphics, and appropriately licensed or public-domain media. **No AI-generated images or video are permitted.** Raw media remains in the ignored top-level `footage/` tree.

## Conventions

Statuses are `planned`, `blocked`, `captured`, and `approved`; `rights-gated` marks optional media that cannot be used without clearance. Asset IDs use `Axx` (A-roll/pickups), `Bxx` (physical B-roll), `Cxx` (screen capture), `Txx` (third party), and `Gxx` (graphics). Filenames use `<asset-id>_<short-description>_<take-or-version>.<ext>` in lowercase (for example `b01_rack-macro_t02.mov`).

## Pre-production gates

- [ ] Resolve every spoken `<...>` placeholder before final recording.
- [ ] Reproduce and retain every AWS calculator input used for the comparison.
- [ ] Sanitize every screen recording: secrets, tokens, private hostnames, personal data, and terminal history.
- [ ] Clear every third-party asset and complete its rights-ledger row.
- [ ] Use the self-recorded **A02** reaction by default; use the *Schitt’s Creek* excerpt **T06** only if appropriately cleared.
- [ ] Lock current/future/hypothetical labels before graphics approval.

## Chronological visual-cue coverage

The cue numbers are the one-based order of the current 42 `[VISUAL]` blocks in `script.md`.

| Cue | Defined asset IDs |
|---|---|
| V01 | B01 T01 T02 T03 G01 |
| V02 | B02 G01 |
| V03 | A01 B04 |
| V04 | A01 G01 |
| V05 | C01 |
| V06 | A02 C01 |
| V07 | A02 T06 |
| V08 | A02 C02 |
| V09 | A01 B01 G02 |
| V10 | G03 |
| V11 | B03 |
| V12 | B02 G04 |
| V13 | C03 |
| V14 | G05 |
| V15 | A03 C04 |
| V16 | A03 C04 T04 G01 |
| V17 | C05 G01 |
| V18 | A04 G06 |
| V19 | A04 G07 |
| V20 | A04 C05 G01 |
| V21 | C06 |
| V22 | C07 |
| V23 | C04 G08 |
| V24 | A05 B03 G04 |
| V25 | B04 G01 |
| V26 | G09 |
| V27 | G10 |
| V28 | C08 G11 |
| V29 | G11 |
| V30 | G11 |
| V31 | G12 |
| V32 | A05 G15 |
| V33 | A05 G15 |
| V34 | B05 G13 |
| V35 | G14 |
| V36 | A06 G15 |
| V37 | A06 B03 |
| V38 | B04 C09 T05 G17 |
| V39 | C04 C05 C06 C07 C10 G01 |
| V40 | A07 B06 G16 |
| V41 | A07 T05 G17 |
| V42 | A07 B07 C10 G18 |

## Final audit

- [ ] V01–V42 each has approved coverage and matches the locked script order.
- [ ] Every used asset ID is defined once in a linked production file.
- [ ] All screen recordings passed the sanitation gate.
- [ ] Rights ledger, receipts, licenses, and required attributions are complete.
- [ ] Current behavior, future plans, and unimplemented hypotheses are unmistakable.
- [ ] Measurement values, AWS inputs, BOM totals, formulas, and dates were independently checked.
- [ ] No AI-generated image/video or uncleared television excerpt appears in the edit.
- [ ] Final filenames follow the convention and raw media remains outside Git.
