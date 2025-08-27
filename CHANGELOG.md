# Changelog

## 2025-08-27
- fix: restore alphabetical order in .wordlist.txt.
- docs: add wordlist regression postmortem and outage records.

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
- fix: validate svg3d shading factor to reject NaN and infinity.
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
