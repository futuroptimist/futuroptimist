# Fuzzing Wins

Incidents uncovered by fuzzing and their postmortems.

- **2025-08-24** – [svg3d non-finite factor](pms/2025-08-24-svg3d-nonfinite-factor.md):
  reject non-finite shading factors to avoid crashes.
- **2025-08-27** – [slugify unicode mishandled](pms/2025-08-27-slugify-unicode.md):
  normalize titles and fallback to `untitled` to keep folders stable.
- **2025-08-27** – [status_to_emoji type crash](pms/2025-08-27-status-emoji-type.md):
  guard against non-string workflow conclusions.
