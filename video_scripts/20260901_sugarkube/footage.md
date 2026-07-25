# Sugarkube Production Asset Index

This is the canonical production index for [`script.md`](script.md). Detailed, nonduplicated assets live in [`production/broll.md`](production/broll.md), [`production/stock.md`](production/stock.md), and [`production/graphics.md`](production/graphics.md).

## Media policy

This production permits original footage, original screen recordings, manually produced graphics, and appropriately licensed or public-domain media. It permits **no AI-generated images or video**. Raw media remains in the ignored top-level `footage/` tree; do not add `assets.json` until matching footage directories exist.

## Conventions

Statuses are `[ ]` planned, `[-]` in progress, `[x]` approved, and `[!]` blocked. Asset IDs use `Axx` for A-roll/pickups, `Bxx` for original physical B-roll, `Cxx` for original screen capture, `Txx` for third-party media, and `Gxx` for manual graphics. Filenames use `<asset-id>_<short-description>_<take-or-version>.<ext>` in lowercase ASCII, for example `b01_rack-macro_t02.mov`.

## Pre-production gates

- [ ] Resolve every spoken `<...>` placeholder before final recording.
- [ ] Reproduce and retain every AWS calculator input and the dated result.
- [ ] Sanitize all screen recordings: secrets, tokens, private hostnames, personal data, and terminal history.
- [ ] Clear every third-party asset and complete its rights-ledger row before edit lock.
- [ ] Use the self-recorded **A04** reaction instead of the *Schitt’s Creek* excerpt unless **T06** is appropriately cleared.
- [ ] Confirm all current, future, and hypothetical claims use the correct graphic label.

## Chronological visual-cue coverage

The cue numbers are the one-based order of the current 42 `[VISUAL]` blocks in `script.md`.

| Cue | Asset IDs | Coverage |
|---|---|---|
| V01 | B01, T01, T02, T03, G01 | Rack macros and illustrative physical cloud infrastructure |
| V02 | B01, G01 | Rack hero and node lower third |
| V03 | A01, B03 | Desk thesis and meter insert |
| V04 | A01, G01 | SRE experience disclosure |
| V05 | C01 | GitHub, CI, terminal, verification, updates, rollback |
| V06 | A01, C01 | Project list, just menu, joke |
| V07 | A04, T06 | Self-recorded reaction default; optional cleared excerpt |
| V08 | A01, C01 | Sanitized agentic-code review and tests |
| V09 | A01, B01, G02 | Cloud/homegrown transition |
| V10 | G03 | Kubernetes placement, restart, rolling update |
| V11 | B01, B02 | Complete rack and office inventory |
| V12 | B01, G04 | Nine-slot current/future/unused state |
| V13 | C02 | Sugarkube files and just workflows |
| V14 | G05 | Current ecosystem and labeled future projects |
| V15 | A02, C03 | DSPACE landing/gameplay and joke |
| V16 | A02, C03, T04, G01 | Quest domains and future 3D caveat |
| V17 | C04, G01 | API, compute app, operator and relay roles |
| V18 | A02, G06 | Ciphertext trust boundary |
| V19 | A02, G07 | Nonexistent reputation hypothesis |
| V20 | A02, C04, G01 | Privacy caveat and sanitized self-hosting evidence |
| V21 | C05 | Three.js portfolio experience |
| V22 | C06 | Text and keyboard experience |
| V23 | C03, G08 | Connected ecosystem and dChat loop |
| V24 | A03, B02, G04 | Pi/RAM lineup and six active nodes |
| V25 | B03, C08, G01 | Disconnect nodes and capture idle/load/peak |
| V26 | G09 | Electricity calculator |
| V27 | B03, G10 | Measurement boundary |
| V28 | C07, G11 | AWS calculator and Oregon failure domain |
| V29 | G11, G16 | Six shape-matched instances |
| V30 | G12 | Storage, IPv4, and exclusions |
| V31 | G13 | Dated AWS pricing table |
| V32 | A03, G16 | Always-on shape-match caveat |
| V33 | A03, G16 | Financial, not energy, comparison |
| V34 | B04, G14 | BOM, redacted receipts, node totals |
| V35 | G15 | Break-even formula and chart |
| V36 | A03, G16 | Lifecycle limitations |
| V37 | A03, B02, G16 | Drink, fans, indirect-water caveat |
| V38 | B03, C08, T05, G18 | Controls, scaling/shutdown, future off-grid goal |
| V39 | C09, G01 | Four-project participation montage |
| V40 | A04, B05, G17 | Start-small alternatives |
| V41 | A04, T05, G18 | Future solar CTA |
| V42 | A04, B06, C09, G19 | Closing montage, ecosystem resolve, hero |

## Final audit

- [ ] Every V01–V42 edit beat has approved coverage and matches the current script order.
- [ ] All spoken placeholders and measurement/pricing placeholders are resolved.
- [ ] AWS inputs, power readings, BOM, and redacted receipt evidence are retained with the project records.
- [ ] Every capture passes the screen-sanitization review.
- [ ] Every Txx item used is cleared, attributed, and recorded in the rights ledger; unused candidates are removed from the edit.
- [ ] No AI-generated image or video, untracked binary, generated `prompter.txt`, or premature `assets.json` is committed.
- [ ] Current behavior, future plans, and unimplemented hypotheses are visibly distinct.
- [ ] Final export uses only approved filenames and the closing hero resolves cleanly.
