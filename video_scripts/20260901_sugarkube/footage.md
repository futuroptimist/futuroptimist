# Sugarkube Footage and Production Index

This is the canonical master index for the [script](script.md), [original production checklist](production/broll.md), [third-party stock ledger](production/stock.md), and [manual graphics checklist](production/graphics.md).

## Media policy

This production permits original footage, original screen recordings, manually produced graphics, and appropriately licensed or public-domain media. It permits **no AI-generated images or video**. Raw media stays in the ignored top-level `footage/` tree; no `assets.json` is created until matching footage directories exist.

## Conventions

- Statuses: `[ ]` planned, `[~]` captured/drafted but not cleared, `[x]` final and cleared, `[!]` blocked.
- Asset IDs are globally unique: `Axx` A-roll/pickups, `Bxx` physical B-roll, `Cxx` screen recordings, `Txx` third-party media, and `Gxx` manually produced graphics.
- Filename: `sugarkube_<asset-id-lower>_<take-or-version>.<ext>` (for example `sugarkube_b01_take03.mov`).
- `V01`–`V42` are the current `[VISUAL]` cues in one-based chronological order; they are cue references, not asset definitions.

## Pre-production gates

- [ ] Resolve every spoken `<...>` placeholder before final recording.
- [ ] Reproduce the AWS calculator estimate and retain/export every calculator input with the project records.
- [ ] Sanitize all screen recordings: secrets, tokens, private hosts, terminal history, personal data, and receipts.
- [ ] Clear every third-party asset and complete its rights-ledger row before editing it in.
- [ ] Use the self-recorded `A02` reaction instead of the *Schitt’s Creek* excerpt unless `T05` is appropriately cleared.
- [ ] Confirm current, future-plan, and unimplemented-hypothesis labels against the script.

## Chronological visual coverage

| Cue | Planned asset IDs |
|---|---|
| V01 | `B01`, `T01`, `T02`, `T03`, `G01` |
| V02 | `B01`, `G01` |
| V03 | `A01`, `B03` |
| V04 | `A01`, `G01` |
| V05 | `C01` |
| V06 | `C01`, `A01` |
| V07 | `A02`, `T05` |
| V08 | `A02`, `C02` |
| V09 | `A01`, `B01`, `G02` |
| V10 | `G03` |
| V11 | `B02` |
| V12 | `B01`, `G04` |
| V13 | `C03` |
| V14 | `G05` |
| V15 | `C04`, `A02` |
| V16 | `C04`, `T04`, `A02`, `G07` |
| V17 | `C05`, `G01` |
| V18 | `G06`, `A03` |
| V19 | `A03`, `G07` |
| V20 | `A03`, `C05` |
| V21 | `C06` |
| V22 | `C06` |
| V23 | `G08`, `C04` |
| V24 | `B02`, `A03`, `G04` |
| V25 | `B03`, `C08` |
| V26 | `G09` |
| V27 | `G10` |
| V28 | `C07`, `G11` |
| V29 | `G11`, `G15` |
| V30 | `G11` |
| V31 | `G12` |
| V32 | `A03`, `G15` |
| V33 | `A03`, `G15` |
| V34 | `B04`, `G13` |
| V35 | `G14` |
| V36 | `A04`, `G15` |
| V37 | `A04`, `B02` |
| V38 | `B03`, `B06`, `C08`, `T06`, `G17` |
| V39 | `C09` |
| V40 | `A04`, `B05`, `G16` |
| V41 | `A04`, `T06`, `G17` |
| V42 | `A04`, `B01`, `B06`, `C09`, `G08` |

## Final audit

- [ ] Every V01–V42 cue has captured/drafted coverage and every referenced ID is defined once.
- [ ] Narration placeholders and measured-value graphics use final verified numbers.
- [ ] AWS inputs, pricing date, exclusions, receipts, BOM, and power readings are retained and reproducible.
- [ ] Every screen and receipt is sanitized; every Txx item is cleared and attributed as required.
- [ ] No AI-generated image/video or uncleared television excerpt appears in the timeline.
- [ ] Future plans and unimplemented hypotheses cannot be mistaken for current behavior.
- [ ] Final export includes the intended lower thirds, caveats, accessibility review, audio mix, captions, and closing hero.
