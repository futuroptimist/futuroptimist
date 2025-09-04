# SRT hour overflow

- **Date**: 2025-09-03
- **Summary**: `parse_srt` skipped captions when hour fields used more than two digits.
- **Root Cause**: The regex expected exactly two digits for the hour component.
- **Resolution**: Permit multi-digit hour values so long-duration captions parse correctly.
- **Lessons**: Fuzz time fields with large values to catch format limits early.
