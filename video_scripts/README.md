# Video scripts

`script.md` is the canonical editorial source for each video. Its Markdown is parsed into the normalized object described by [`schemas/video_script.schema.json`](../schemas/video_script.schema.json).

## Canonical format

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

Use `Transcript for video` instead of `Draft script for video` for a transcript. An outline, section headings, and visual cues are optional. Every body block must be a `###` section, narrator, or visual block; blocks have one blank line between them and files have exactly one final newline. Inline Markdown and narrator timing comments are preserved in `script.md`.

Run `make check_scripts` (read-only) before committing, or `make format_scripts` to migrate structural legacy formatting. The formatter discovers nested scripts, including `drafts/`.

## Prompter export

Run `make prompter SLUG=20260901_sugarkube ALLOW_PLACEHOLDERS=1`, or:

```bash
python video_scripts/export_prompter.py --slug 20260901_sugarkube --allow-placeholders
```

`prompter.txt` is ignored generated output and never replaces `script.md`. Visual directions, headings, timing comments, and Markdown formatting are removed. When visual cues exist, narration preceding each cue is grouped into that visual beat (42 chapters for the current Sugarkube script); transcript-only scripts use one chapter per narrator segment. Exactly one blank line separates Prompter chapters. Exports reject spoken `<...>` placeholders unless `--allow-placeholders` is supplied. `--script PATH` and `--output PATH` select custom paths.

## Production planning

A video's `footage.md` is its canonical production index and may link detailed files under `production/`. Raw recordings and media stay under the ignored top-level `footage/` tree; do not add `assets.json` until corresponding footage directories exist.
