# Fuzzing Wins

Incidents uncovered by fuzzing and their postmortems.

- **2025-08-24** – [svg3d non-finite factor](pms/2025-08-24-svg3d-nonfinite-factor.md):
  reject non-finite shading factors to avoid crashes.
- **2025-08-27** – [Reversed SRT times](pms/2025-08-27-reversed-srt-times.md):
  ignore captions where start ≥ end to avoid negative durations.
