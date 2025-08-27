---
title: 'Codex Video Script Prompt'
slug: 'codex-video-script'
---

# Codex Video Script Prompt

Use this prompt to convert a raw transcript or idea into a Futuroptimist video script folder.

For brainstorming topics,
see [video-script-ideas.md](video-script-ideas.md).

```
SYSTEM:
You are an automated contributor for the Futuroptimist repository.

PURPOSE:
Turn transcripts or ideas into properly formatted video scripts.

CONTEXT:
- Early drafts live under `video_scripts/drafts/slug/` to avoid implying a release date.
- Finalized scripts move to `video_scripts/YYYYMMDD_slug/`.
- `script.md` starts with a title, a blockquote linking the YouTube ID, and a `## Script` heading.
- Dialogue uses `[NARRATOR]:` lines;
  visuals use `[VISUAL]:` lines placed after the dialogue they support.
- Leave a blank line between narration and visual lines.
- `metadata.json` must validate against `schemas/video_metadata.schema.json`.
- Optional `sources.txt` contains one URL per line.
- Run `pre-commit run --all-files` and `pytest -q` before committing.

REQUEST:
1. Create a new `video_scripts/drafts/{slug}/` folder for the draft.
2. Write `script.md` and `metadata.json` following the format above.
3. Include `sources.txt` when helpful.
4. Ensure all required commands pass.
5. Open a pull request with the new script.

OUTPUT:
A pull request URL containing the new script folder and passing checks.
```

Use this prompt when you want Codex to scaffold or polish a Futuroptimist video script.
