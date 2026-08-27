# Video script workflow

Each episode's `script.md` is the canonical editorial source. It is parsed into the normalized object validated by `schemas/video_script.schema.json`; use `python src/video_script_format.py --check video_scripts` (or `make check_scripts`) to validate all nested scripts and `--write` (or `make format_scripts`) to migrate supported legacy structure.

## Canonical Markdown

```markdown
# Video title

> Draft script for video `video-id-or-placeholder`

## Outline

- Optional outline entry

## Script

### Optional section heading

[NARRATOR]: One complete spoken thought.

[VISUAL]: The visual direction supporting that narration.
```

`Transcript` may replace `Draft script`; outline, section, and visual blocks are optional. Every body block is a one-line `###` section, `[NARRATOR]:`, or `[VISUAL]:` block separated by one blank line. Inline emphasis and narrator timing comments remain in `script.md`.

## Prompter exports

`prompter.txt` is generated and ignored, never canonical. Run:

```bash
python video_scripts/export_prompter.py --slug 20260901_sugarkube --allow-placeholders
make prompter SLUG=20260901_sugarkube ALLOW_PLACEHOLDERS=1
```

The exporter removes directions and Markdown presentation syntax. Blank lines separate Prompter chapters. Scripts with visuals—including Sugarkube—group each narration run by the following visual beat; transcript-only scripts use one narrator segment per chapter. Normal exports reject spoken `<...>` placeholders; `--allow-placeholders` is for rehearsal only. Use `OUTPUT=path` or `--output PATH` for a custom destination.

## Production planning

An episode's `footage.md` is its production-plan master index and may link focused files under `production/`. Raw media stays in the ignored top-level `footage/` tree. Do not add `assets.json` before matching media directories exist.

To combine those linked plans into a printable checklist, run `make production_pdf
SLUG=latest` or supply an exact eligible slug. `OUTPUT=path` and
`PAGE_SIZE=letter|a4` are optional; the default is
`dist/production-pdfs/<resolved-slug>-production-checklist.pdf`. Use
`python src/render_production_pdf.py --list` to see eligible slugs and the current
`latest` mapping. Eligibility requires at least one direct Markdown file in the
episode's `production/` directory.

The **Production Plan PDF** Actions workflow accepts `latest` or an exact slug in
its required text field. `latest` is resolved only after checkout to the newest
eligible datestamped directory, so the resolved slug cannot appear in the dispatch
field before the run. The logs and job summary report it. The run artifact contains
the PDF and GitHub downloads that artifact as an archive.
