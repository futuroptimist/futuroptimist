# Video script workflow

Each episode's `script.md` is the canonical editorial source. It follows [`schemas/video_script.schema.json`](../schemas/video_script.schema.json): one H1, one canonical draft/transcript blockquote, optional `## Outline`, `## Script`, and blank-separated `###` section, `[NARRATOR]:`, or `[VISUAL]:` blocks. Transcript-only scripts are supported.

```bash
python src/video_script_format.py --check video_scripts
python src/video_script_format.py --write video_scripts
make check_scripts
make format_scripts
```

`--check` is read-only. Use `--write` deliberately to migrate or format scripts, then review the content-preserving diff.

## Prompter export

`prompter.txt` is generated, ignored output; never edit it instead of `script.md`.

```bash
python video_scripts/export_prompter.py --slug 20260901_sugarkube --allow-placeholders
make prompter SLUG=20260901_sugarkube ALLOW_PLACEHOLDERS=1
```

The exporter strips Markdown and retains only spoken narration. Exactly one blank line separates Prompter chapters. For scripts with visuals—including Sugarkube—it groups each run of narration by the following visual beat; transcript-only scripts use one narrator segment per chapter. By default unresolved `<...>` speech placeholders fail before an output is written.

## Production planning

An episode may use `footage.md` as its master plan and link detailed files under `production/`. Raw photos, audio, and video remain in the ignored top-level `footage/` tree; do not create `assets.json` until matching footage directories exist.
