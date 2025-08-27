# unsorted wordlist regression

- Date: 2025-08-27
- Author: codex
- Status: resolved

## Background
`.wordlist.txt` supplies custom vocabulary for spellcheck and style tooling.

## Root cause
New terms were added without preserving alphabetical order, triggering `test_wordlist_is_alphabetized` during `pytest`.

## Detailed explanation
Sorting guarantees deterministic linting and prevents duplicate entries. An unsorted word list breaks the unit test guarding it.

## Impact
CI tests failed, blocking merges until the list was corrected.

## Action items
### Prevent
- Sort and deduplicate `.wordlist.txt` after inserting new words.

### Detect
- Retain the alphabetization test.

### Mitigate
- Restored alphabetical order and removed duplicates.
