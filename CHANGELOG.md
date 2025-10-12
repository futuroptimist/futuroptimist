## Unreleased
- fix: classify unknown report_funnel selects as `other` so manifests stay faithful.
- test: cover fallback classification for report_funnel selects.
- feat: record YouTube view counts when enriching metadata.
- test: require live metadata to expose positive view_count values.
- docs: note the view_count sync in INSTRUCTIONS, llms.txt, and the
  video editing playbook publish checklist.
- feat: tag report_funnel directory selects with a dedicated kind so manifests stay
  faithful to their inputs.
- feat: add thumbnail text predictor CLI for CTR heuristics.
- test: assert directory selects are labelled explicitly and cover predictor scoring
  and reasoning heuristics.
- docs: note the new directory classification in INSTRUCTIONS and reference the
  predictor helper in the video editing playbook.

- feat: store HTTPS YouTube thumbnail URLs in live metadata files.
- test: enforce live thumbnails point at YouTube via metadata schema tests.
- docs: note the thumbnail URL check in INSTRUCTIONS and video editing playbook.

## 2025-10-10
- feat: add rename_video_slug helper to rename script and footage slugs.
- test: cover slug rename workflow.
- docs: document the rename helper and roadmap update.

## 2025-10-08
- chore: add pre-commit hook to validate outage JSON schema and add regression tests.
- feat: expand collect_sources overrides to resolve `~` and env variables.
- test: cover collect_sources override expansion cases.
- docs: reference the new override tests in INSTRUCTIONS.

## 2025-09-03
- fix: handle missing npm in checks script and ensure trailing newline.
- test: verify checks script handles missing npm and newline.
- chore: remove obsolete heatmap workflow and artifacts.
- fix: allow multi-digit hour fields in `parse_srt` for very long videos.
- fix: compare SRT timestamps numerically to keep captions across 99h boundary.
- test: cover SRT parsing with hours beyond 99.
- docs: record SRT hour overflow outage and postmortem.
- fix: parse SRT entries lacking numeric index.
- test: cover SRT parsing without sequence numbers.
- docs: note optional SRT sequence numbers.

## 2025-09-02
- fix: set up Python before uv in docs workflow.
- docs: record docs workflow outage.
- docs: consolidate outage records under outages/.
- fix: pin rawpy to 0.25.1 to ensure Python 3.12 wheels.
- test: assert rawpy requirement is pinned.
- docs: record test suite outage for rawpy pin.
- fix: treat 'action_required' status as failure in repo_status.

## 2025-09-01
- chore: drop pyheif dependency and simplify HEIF conversion.
- fix: bump rawpy to avoid Python 3.12 build failures.
- docs: record rawpy wheel outage.

## 2025-08-27
- feat: detect fine-grained GitHub tokens in scan-secrets script.
- chore: whitelist project jargon for spellcheck.
- chore: resort `.wordlist.txt` to fix failing wordlist test.
- docs: add outage record and postmortem for wordlist sorting regression.

## 2025-08-25
- fix: treat 'startup_failure' status as failure in repo_status.
- fix: replace invalid UTF-8 bytes when parsing SRT files to prevent crashes.
- test: cover invalid UTF-8 SRT input.
- chore: alphabetize `.wordlist.txt`.
- docs: record SRT decoding incident and postmortem.
- fix: alphabetize and deduplicate .wordlist.txt to keep tests green.
- docs: add wordlist postmortem and outage record.
- fix: normalize whitespace in status_to_emoji.

## 2025-08-24
- fix: remove stray prompt text from tests workflow to restore CI.
- test: verify all workflow files parse as valid YAML.
- docs: record tests workflow outage and postmortem.
- fix: treat 'canceled' status as failure in repo_status.
- fix: ensure index_local_media writes newline at end of file.
- feat: detect GitHub tokens in scan-secrets script.
- fix: ensure scaffold_videos writes metadata.json with trailing newline.

## 2025-08-23
- fix: add missing workflow field to outage record to restore CI.
- fix: treat 'timed out' variants as failures in status_to_emoji.
- test: require outage entries to reference schema and fix missing pointer.
- chore: set up Python before installing dependencies in test workflow.
- fix: install dependencies in uv-managed venv to avoid permission errors.

## 2025-08-22
- chore: skip Codecov upload when token is missing to prevent CI failures.
