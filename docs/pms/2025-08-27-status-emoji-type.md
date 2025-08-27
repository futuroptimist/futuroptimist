# status_to_emoji type crash

- **Date**: 2025-08-27
- **Summary**: Fuzzing repo_status.status_to_emoji with random objects revealed that passing a non-string value raised an AttributeError.
- **Impact**: A malformed API response could crash tooling that maps workflow conclusions to emojis.
- **Root Cause**: status_to_emoji assumed the conclusion was always a string and called `.strip()` unconditionally.
- **Resolution**: Guard the function against non-string inputs by returning "❓" when the value is not a string. Added a regression test.
- **Lessons Learned**: Validate external data types before processing.
- **Links**: [Outage record](../../outages/2025-08-27-status-emoji-type.json)
