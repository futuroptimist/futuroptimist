# Fuzzing Wins

Incidents uncovered by fuzzing and their postmortems.

- **2025-08-27** – [Reversed SRT times](../outages/2025-08-27-reversed-srt-times.md):
  ignore captions where start ≥ end to avoid negative durations.
- **2025-08-27** – [status_to_emoji type crash](../outages/2025-08-27-status-emoji-type.md):
  guard against non-string workflow conclusions.
