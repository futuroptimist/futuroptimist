# Reversed SRT times

- **Date**: 2025-08-27
- **Summary**: `parse_srt` allowed captions where the start time was after the end time, creating negative-duration entries.
- **Root Cause**: The parser missed validation for non-increasing timecodes.
- **Resolution**: Ignore caption entries with start times greater than or equal to their end times.
- **Lessons**: Fuzz timestamp order to catch reversed ranges early.
