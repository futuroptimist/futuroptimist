# Video script workflow

`script.md` is the canonical, reviewable source for every video. It is parsed into the normalized object defined by [`video_script.schema.json`](../schemas/video_script.schema.json). Use one H1, one canonical draft/transcript blockquote, an optional `## Outline`, then `## Script`; script blocks are optional `###` sections or nonempty, single-line `[NARRATOR]:` and `[VISUAL]:` segments separated by one blank line.

```bash
python src/video_script_format.py --check video_scripts
python src/video_script_format.py --write video_scripts
python video_scripts/export_prompter.py --slug 20260901_sugarkube
```

The formatter's check mode is read-only; write mode migrates known legacy structure. `prompter.txt` is generated and ignored. Its blank-line-separated paragraphs become Prompter chapters: visual scripts group each narration run by the following visual beat (42 beats for Sugarkube), while transcript-only scripts use one narrator segment per chapter. Rehearsals may pass `--allow-placeholders`, but final recording must not.

Production planning belongs in each video's `footage.md` and any linked `production/` checklists. Raw media stays in the ignored top-level `footage/` tree, not beside the Markdown plans.
