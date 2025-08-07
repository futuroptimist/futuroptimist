# 3-D LOC Heatmap Design

This document captures the plan for replacing the simple PR heatmap with a pseudo
3‑D chart that encodes **lines of code** changed per day. It mirrors the design
shared in chat and explains how the feature slots into this repository.

## Visual concept
- Layout matches GitHub's 7×53 grid of weeks and weekdays.
- Each cell becomes an isometric bar whose height scales with `log10(LOC)`.
- Dual SVGs are generated for light and dark themes and swapped using the
  `prefers-color-scheme` media query.
- Optionally each bar links back to its contribution detail page.

## Data pipeline
1. Fetch commits and PRs authored by `futuroptimist` using the GitHub GraphQL
   API (`contributionsCollection`).
2. For every commit, retrieve the `additions` and `deletions` via the REST API
   and sum them per day.
3. Cache commit stats in `assets/heatmap_data.json` to stay inside rate limits. If the file
   becomes corrupted, it's ignored and rebuilt on the next run.
4. Render the SVGs with `svgwrite` and commit them via the workflow.

## Implementation outline
Files introduced by this feature:
```
.github/workflows/contrib-heatmap.yml   # updated with write permissions
src/generate_heatmap.py                 # main entrypoint
src/gh_graphql.py                       # GraphQL helper with retries
src/gh_rest.py                          # commit → LOC cache
src/svg3d.py                            # draw isometric bars
assets/heatmap_light.svg                # auto-generated
assets/heatmap_dark.svg                 # auto-generated
```
The nightly workflow installs `svgwrite`, runs `generate_heatmap.py` and then
commits the updated SVGs.

A snippet in `README.md` embeds the graphic:
```md
### LOC-weighted contribution heat-map
<p align="center">
  <picture>
    <source srcset="assets/heatmap_dark.svg" media="(prefers-color-scheme: dark)">
    <img src="assets/heatmap_light.svg" alt="Lines-of-code contributions past year">
  </picture>
</p>
```
