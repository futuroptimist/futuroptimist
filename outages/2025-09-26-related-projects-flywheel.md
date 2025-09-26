# Related Projects flywheel false alarm

- **Date**: 2025-09-26
- **Summary**: The hourly status updater marked the flywheel repo as failing even though the latest
  workflow rerun succeeded.
- **Impact**: The README's Related Projects section showed a ❌ badge for flywheel, creating a false
  perception that the template was unhealthy.
- **Root Cause**: `fetch_repo_status` treated any historical failure for a commit as authoritative,
  even when a newer rerun of the same workflow succeeded.
- **Resolution**: Deduplicate workflow runs by workflow/run number and keep only the most recent
  attempt before evaluating the conclusion. Added a regression test and verified the API now reports
  ✅ for `futuroptimist/flywheel`.
- **Lessons Learned**: When sampling GitHub Actions history, collapse reruns so stale data cannot
  override the current signal.
- **Links**: [Outage record](2025-09-26-related-projects-flywheel.json)
