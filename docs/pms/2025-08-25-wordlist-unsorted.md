# unsorted wordlist broke tests

- Date: 2025-08-25
- Author: codex
- Status: resolved

## Background
`.wordlist.txt` supplies custom vocabulary for spellcheck and style tools.

## Root cause
New words were appended to the file without maintaining alphabetical order, leaving duplicate entries at the end of the list. The `test_wordlist_is_alphabetized` check detected the misordering and failed.

## Detailed explanation
The repository enforces a sorted `.wordlist.txt` to keep contributions consistent. Manual edits bypassed this convention, producing unsorted and repeated lines. Pytest compared the file to its sorted version and raised an assertion, halting the test suite.

## Impact
Developers could not rely on the test suite, and CI would reject commits until the word list was fixed.

## Action items
### Prevent
- Sort and deduplicate `.wordlist.txt` after adding new terms.

### Detect
- Keep the word list sorting test in place.

### Mitigate
- Alphabetized and deduplicated the word list.
