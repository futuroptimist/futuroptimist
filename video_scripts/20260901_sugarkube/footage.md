# Sugarkube Production Asset Index

This is the canonical master index for the [script](script.md), with nonduplicated asset definitions in [original B-roll and recordings](production/broll.md), [third-party stock](production/stock.md), and [manual graphics](production/graphics.md).

This production permits **original footage, original screen recordings, manually produced graphics, and appropriately licensed or public-domain media**. It permits **no AI-generated images or video**.

## Conventions

- Statuses: `[ ]` planned, `[-]` captured/drafted but not cleared, `[x]` verified and edit-ready, `[!]` blocked.
- Asset IDs: `Axx` A-roll/pickups, `Bxx` original physical B-roll, `Cxx` original screen recordings, `Txx` third-party assets, and `Gxx` manual graphics.
- Filenames: `<asset-id>_<short-description>_<take-or-version>.<ext>`, lowercase kebab-case after the uppercase ID (for example, `B01_rack-macro_t03.mov`). Raw media stays in the ignored top-level `footage/` tree.
- Cue IDs `V01`–`V42` are the current `[VISUAL]` blocks in one-based script order. If cues change, update this table and its deterministic test in the same commit.

## Pre-production gates

- [ ] Resolve every spoken `<...>` placeholder before final recording.
- [ ] Reproduce and retain every AWS calculator input used for the comparison.
- [ ] Sanitize all screen recordings: secrets, tokens, private hostnames, personal data, terminal history, and unrelated notifications.
- [ ] Clear every third-party asset in the rights ledger before edit lock.
- [ ] Use the self-recorded **A02** reaction instead of the *Schitt's Creek* excerpt unless **T06** is appropriately cleared.
- [ ] Confirm current, future, and unimplemented/hypothetical claims use distinct labels.
- [ ] Confirm no AI-generated image or video enters the production.

## Chronological visual coverage

| Cue | Script beat | Asset IDs |
|---|---|---|
| V01 | Rack macro opening and illustrative physical cloud infrastructure | B01, T01, T02, T03, G01 |
| V02 | Clean rack hero and node lower-third | B02, G01 |
| V03 | Desk thesis, meter insert, and caveat | A01, B02 |
| V04 | SRE experience label without private material | A01, G01 |
| V05 | GitHub, CI, deploy, verify, update, and rollback | C01 |
| V06 | Public project list, `just --list`, joke, and thesis | C01, A01 |
| V07 | Agentic disclosure and default self-recorded reaction | A02, T06 |
| V08 | Real agentic workflow and human verification | A02, C02 |
| V09 | Rack transition and managed-versus-homegrown title | B01, G02 |
| V10 | Kubernetes placement, restart, and rolling update | G03 |
| V11 | Rack, Pis, tiers, switch, cables, storage, fans, placement | B03 |
| V12 | Nine-slot current/future/unassigned state | B04, G04 |
| V13 | Sugarkube files and `just` lifecycle workflows | C03, C04 |
| V14 | Current three-project ecosystem and future placeholder | G05 |
| V15 | DSPACE landing/gameplay and space joke | C05, A03 |
| V16 | DSPACE domains, quest tree, unfinished and future-3D caveat | C05, T04, A03, G06 |
| V17 | token.place API, desktop node, and operator workflow | C07, C08, G01 |
| V18 | token.place trust boundary and caveat | G07, A04 |
| V19 | Explicitly unimplemented reputation hypothesis | A04, G08 |
| V20 | Privacy caveat, self-hosting interfaces, and redacted logs | A04, C08 |
| V21 | danielsmith.io immersive house experience | C09 |
| V22 | danielsmith.io text and keyboard experience | C10 |
| V23 | Connected ecosystem, dChat, and feedback loop | G09, C06 |
| V24 | Pi/RAM lineup, six active nodes, and joke | B03, B04, A05, G04 |
| V25 | Disconnect unused nodes and record idle/load/peak boundary | B05, B06, B07, A05, G01 |
| V26 | Electricity calculator with pending measured values | G10 |
| V27 | Included and excluded measurement boundary | B06, G11 |
| V28 | AWS calculator and single-AZ architecture | C11, G12 |
| V29 | Six c7g.xlarge shape-matched instances | C11, G12, G16 |
| V30 | gp3, IPv4, and managed-service exclusions | C11, G12 |
| V31 | Dated AWS pricing snapshot and exclusions | C11, G13 |
| V32 | Always-on shape-match caveat | A06, G16 |
| V33 | Financial, not watt-for-watt energy, comparison | A06, G16 |
| V34 | Hardware, printed parts, BOM, receipts, and totals | B08, C15, G14 |
| V35 | Break-even formula, crossing chart, and no-break-even case | G15 |
| V36 | Lifecycle and ignored-factor limitations | A06, G16 |
| V37 | Drink joke, cooling, and indirect-water caveat | A07, B13, G16 |
| V38 | Meter/control, operational shutdown, and future off-grid hardware | B07, B09, C12, T05, G18 |
| V39 | Four-project participation montage | A08, C13, G01 |
| V40 | One-Pi, old-computer, full-rack, start-small Kubernetes | A08, B10, B11, B12, G17 |
| V41 | Future solar/battery/inverter CTA | A09, T05, G18 |
| V42 | Closing performance, deployments, ecosystem resolve, and hero | A10, C14, G18, B14 |

## Final audit

- [ ] The script still contains exactly 42 visual cues and this table maps each once.
- [ ] Every table asset ID is defined exactly once in a linked detail file.
- [ ] All original captures are backed up, named conventionally, and logged.
- [ ] Screen recordings passed a frame-by-frame sanitation review.
- [ ] AWS inputs, meter logs, workload notes, BOM, and redacted receipts are retained.
- [ ] Every used third-party item has a complete, cleared rights-ledger row and required attribution.
- [ ] T06 is omitted unless cleared; A02 is the default reaction.
- [ ] Current behavior, future plans, and unimplemented hypotheses are visibly distinct.
- [ ] No AI-generated images/video, generated Prompter export, binary media, or premature `assets.json` is committed.
