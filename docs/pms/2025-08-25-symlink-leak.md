# index_local_media leaked symlink targets

- Date: 2025-08-25
- Author: codex
- Status: resolved

## Background
`scan_directory` builds a JSON index of local media files.

## Root cause
`path.is_file()` follows symlinks, so `scan_directory` recorded files outside the
base directory when symlinks pointed elsewhere.

## Detailed explanation
Fuzzing created a symlink to an external file. The scanner treated the symlink as a
regular file and exposed its metadata in `footage_index.json`, enabling path traversal.

## Impact
Malicious symlinks could leak paths and sizes of files outside the intended tree.

## Action items
### Prevent
- Skip symlinked paths during directory scan.

### Detect
- Add regression test to ensure symlinks are ignored.

### Mitigate
- Document the behavior in the changelog and postmortem.

