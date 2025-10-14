#!/usr/bin/env sh
set -eu

# Normalize to repo root
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
TARGET_DIR="$REPO_ROOT/docs/prompts/codex"

mkdir -p "$TARGET_DIR"

# Gather candidate markdown files that look like prompt docs outside the target dir.
# We consider files within docs/ whose path or filename contains "prompt" or "codex".
# Skip the canonical directory to keep idempotency on repeated runs.
find "$REPO_ROOT/docs" -type f -name '*.md' \
  ! -path "$TARGET_DIR/*" \
  | while IFS= read -r source_path; do
    case "$source_path" in
      *prompts/codex/*) continue ;;
    esac

    base_name=$(basename "$source_path")
    case "$base_name" in
      prompt-docs-summary.md|prompt-saturation-rubric.md) continue ;;
    esac
    dir_name=$(dirname "$source_path")

    # Determine whether the file is a prompt doc based on its directory or filename.
    case "$dir_name/$base_name" in
      *prompts/*|*prompt*|*codex*) : ;;
      *) continue ;;
    esac

    # Remove redundant terms from the filename while keeping the extension intact.
    stem=${base_name%.*}
    ext=${base_name##*.}
    sanitized_stem=$(printf '%s' "$stem" \
      | sed -e 's/[Pp][Rr][Oo][Mm][Pp][Tt][Ss]\?//g' \
            -e 's/[Cc][Oo][Dd][Ee][Xx]//g' \
            -e 's/--*/-/g' \
            -e 's/^-\|-$//g')

    # Fallback to the original stem if the sanitization removed everything meaningful.
    if [ -z "$sanitized_stem" ]; then
      sanitized_stem="$stem"
    fi

    destination="$TARGET_DIR/$sanitized_stem.$ext"

    # If the destination already contains identical content, remove the duplicate source.
    if [ -f "$destination" ] && cmp -s "$source_path" "$destination"; then
      rm -f "$source_path"
      continue
    fi

    # If a file already exists at the destination with different content, keep both by
    # appending a numeric suffix to avoid destructive overwrites.
    if [ -f "$destination" ] && ! cmp -s "$source_path" "$destination"; then
      i=2
      while [ -f "$TARGET_DIR/$sanitized_stem-$i.$ext" ]; do
        i=$((i + 1))
      done
      destination="$TARGET_DIR/$sanitized_stem-$i.$ext"
    fi

    # Ensure parent directory exists and move the file.
    mkdir -p "$(dirname "$destination")"
    mv "$source_path" "$destination"
  done

# Finally, ensure filenames within the target directory drop redundant segments even if they
# were already placed there manually.
find "$TARGET_DIR" -maxdepth 1 -type f -name '*.md' | while IFS= read -r existing; do
  base=$(basename "$existing")
  stem=${base%.*}
  ext=${base##*.}
  sanitized=$(printf '%s' "$stem" \
    | sed -e 's/[Pp][Rr][Oo][Mm][Pp][Tt][Ss]\?//g' \
          -e 's/[Cc][Oo][Dd][Ee][Xx]//g' \
          -e 's/--*/-/g' \
          -e 's/^-\|-$//g')
  [ -n "$sanitized" ] || sanitized="$stem"
  new_path="$TARGET_DIR/$sanitized.$ext"
  if [ "$existing" != "$new_path" ]; then
    if [ -f "$new_path" ] && ! cmp -s "$existing" "$new_path"; then
      i=2
      while [ -f "$TARGET_DIR/$sanitized-$i.$ext" ]; do
        i=$((i + 1))
      done
      new_path="$TARGET_DIR/$sanitized-$i.$ext"
    fi
    mv "$existing" "$new_path"
  fi
done

printf 'Prompt docs consolidated under %s\n' "$TARGET_DIR"
