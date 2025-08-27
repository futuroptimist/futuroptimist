# slugify unicode mishandled

- Date: 2025-08-27
- Author: codex
- Status: resolved

## Background
`slugify` turns video titles into directory-friendly names.

## Root cause
Unicode-only titles normalized to an empty string, producing folders like `20250827_`.

## Detailed explanation
Regular expressions stripped non-ASCII characters without first converting them,
so languages using accents or symbols lost all content. The scaffold script then
created directories with missing slugs, confusing downstream tools.

## Impact
Generated video script folders were misnamed, making automation brittle.

## Action items
### Prevent
- Normalize Unicode to ASCII before slugification.

### Detect
- Fuzz test `slugify` with random Unicode input.

### Mitigate
- Provide `untitled` fallback when slug collapses to nothing.
