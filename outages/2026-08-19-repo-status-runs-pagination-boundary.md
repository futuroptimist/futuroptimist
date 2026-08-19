# Update Repo Status showing "?" for repos with noisy Actions history

- **Date**: 2026-08-19
- **Summary**: The "Related Projects" dashboard on the `futuroptimist` GitHub profile README
  showed ❓ for `token.place` and `flywheel` even though both repos had recent, green CI.
- **Root Cause**: `fetch_repo_status_details()`'s commit lookback in `src/repo_status.py` only
  fetched another page of `/actions/runs` when it also fetched another page of `/commits`. A real,
  non-bot commit that was still on the *first* commits page but whose matching CI runs were buried
  behind frequent, non-CI-signal workflow runs (this dashboard's own hourly commits for `flywheel`,
  a chatty PR-comment-triggered `claude.yml` workflow for `token.place`) never triggered a wider
  runs window, so the walk gave up and reported "unknown" immediately. Confirmed live against the
  GitHub API: `flywheel`'s most recent merge commit had 9 completed, all-green CI runs, but they
  only appeared on runs-page 3 of the branch's completed-runs listing.
- **Resolution**: Track the runs-page cursor independently of the commits-page cursor. When the
  walk reaches a real, unresolved commit and nothing has been selected yet, fetch another runs
  page (up to the existing lookback cap) and retry that same commit before treating it as the
  lookback boundary.
- **Lessons**: Pagination windows that are supposed to grow together should be checked
  independently when one side can legitimately need to grow faster than the other -- a repo's
  automation traffic (bots, chat-driven CI, hourly jobs) can make the "runs" side much noisier
  than the "commits" side.

## Follow-up

- Added regression tests covering a real commit still on commits-page 1 whose runs are buried on a
  later runs page, and confirming the widened runs pagination still respects the shared lookback
  cap.
