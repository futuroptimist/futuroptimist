# wordlist sorting regression

- Date: 2025-08-27
- Author: codex
- Status: resolved

## What went wrong
The custom spellcheck word list `.wordlist.txt` contained an out-of-order entry.

## Root cause
`gitignored` was inserted ahead of `github`, violating the alphabetical constraint enforced by `test_wordlist_is_alphabetized`.

## Impact
The Test Suite workflow failed, blocking CI for new commits.

## Actions to take
- Sort and deduplicate `.wordlist.txt` after adding new terms.
- Keep `test_wordlist_is_alphabetized` to detect regressions early.
