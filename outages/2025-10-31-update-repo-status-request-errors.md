# Update Repo Status workflow crashed on GitHub API errors

- **Date**: 2025-10-31
- **Summary**: `Update Repo Statuses` failed on every hourly cron because transient GitHub API
  errors bubbled out of `src/repo_status.py`.
- **Impact**: README badges and the timestamp in "Related Projects" stopped refreshing, leaving
  stale CI signals for downstream repos.
- **Root Cause**: `fetch_repo_status` called the GitHub REST API without handling
  `requests` exceptions or JSON parsing errors, so any 5xx, timeout, or malformed payload raised
  an exception that terminated the workflow.
- **Resolution**: Wrap the API calls in defensive error handling that logs the failure and falls
  back to the unknown emoji (`❓`) instead of crashing the job.
- **Lessons**: Dashboard scrapers should degrade gracefully on transient API failures so scheduled
  jobs keep running, even if they have to surface "unknown" status temporarily.
- **Links**: [Workflow run](https://github.com/futuroptimist/futuroptimist/actions/runs/19053271543),
  [Outage record](2025-10-31-update-repo-status-request-errors.json)

## Follow-up

- Added regression tests covering request failures and malformed payloads so future changes keep
  returning `❓` instead of raising when GitHub responds with errors.
