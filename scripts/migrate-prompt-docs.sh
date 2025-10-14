#!/usr/bin/env sh
set -eu

# Migrate prompt docs into docs/prompts/codex/ and normalize filenames.
REPO_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TARGET_DIR="$REPO_ROOT/docs/prompts/codex"

mkdir -p "$TARGET_DIR"

# Find markdown files that look like prompt docs outside the target folder.
find "$REPO_ROOT" -type f -name '*.md' \
  \( -iname '*prompt*.md' -o -path "$REPO_ROOT/docs/prompts/*" \) \
  ! -path "$TARGET_DIR/*" \
  ! -name 'prompt-docs-summary.md' \
  | while IFS= read -r SRC; do
    # Skip empty lines from find output.
    [ -n "$SRC" ] || continue

    BASENAME=$(basename "$SRC")
    STEM=${BASENAME%.md}

    NORMALIZED=$(printf '%s' "$STEM" \
      | sed -E 's/[Pp]rompts?//g' \
      | sed -E 's/[Cc]odex//g' \
      | sed -E 's/__+/_/g' \
      | sed -E 's/--+/-/g' \
      | sed -E 's/-_+/-/g' \
      | sed -E 's/_-+/_/g' \
      | sed -E 's/[-_]+$//' \
      | sed -E 's/^[-_]+//' )

    [ -n "$NORMALIZED" ] || NORMALIZED="$STEM"

    DEST="$TARGET_DIR/$NORMALIZED.md"

    # Skip if the source is already at the destination.
    if [ "$SRC" = "$DEST" ]; then
      continue
    fi

    # Ensure the destination directory exists.
    mkdir -p "$(dirname "$DEST")"

    if [ -e "$DEST" ]; then
      if cmp -s "$SRC" "$DEST"; then
        rm -f "$SRC"
        printf 'Removed duplicate prompt doc: %s\n' "${SRC#$REPO_ROOT/}"
      else
        printf 'Skipping %s; destination %s already exists.\n' \
          "${SRC#$REPO_ROOT/}" "${DEST#$REPO_ROOT/}" >&2
      fi
      continue
    fi

    printf 'Moving %s -> %s\n' "${SRC#$REPO_ROOT/}" "${DEST#$REPO_ROOT/}"
    mv "$SRC" "$DEST"
  done
