# SRT hour overflow

- **Date**: 2025-09-03
- **Summary**: `parse_srt` skipped captions when hour fields used more than two digits and dropped entries crossing the 99h boundary.
- **Root Cause**: The regex expected exactly two-hour digits and timestamps were compared as strings.
- **Resolution**: Permit multi-digit hour values and compare times numerically so long-duration captions parse correctly.
- **Lessons**: Fuzz time fields with large values to catch format limits early.
