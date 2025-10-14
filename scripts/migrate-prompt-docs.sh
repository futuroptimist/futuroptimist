#!/usr/bin/env sh
set -eu

# Consolidate Codex prompt docs under docs/prompts/codex/ while normalising filenames.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
TARGET_DIR="$REPO_ROOT/docs/prompts/codex"

mkdir -p "$TARGET_DIR"

changed=0

sanitize_stem() {
  stem=$1
  printf '%s' "$stem" |
    sed -e 's/[Pp][Rr][Oo][Mm][Pp][Tt][Ss]\?//g' \
        -e 's/[Cc][Oo][Dd][Ee][Xx]//g' \
        -e 's/[ _]/-/g' \
        -e 's/-\{2,\}/-/g' \
        -e 's/^-\|-$//g'
}

move_doc() {
  src=$1
  base=$(basename "$src")
  stem=${base%.*}
  ext=${base##*.}
  sanitized=$(sanitize_stem "$stem")
  [ -n "$sanitized" ] || sanitized=$stem
  dest="$TARGET_DIR/$sanitized.$ext"

  # Avoid redundant moves.
  if [ "$src" = "$dest" ]; then
    return
  fi

  if [ -f "$dest" ]; then
    if cmp -s "$src" "$dest"; then
      rm -f "$src"
      changed=1
      return
    fi
    i=2
    while [ -f "$TARGET_DIR/$sanitized-$i.$ext" ]; do
      i=$((i + 1))
    done
    dest="$TARGET_DIR/$sanitized-$i.$ext"
  fi

  mv "$src" "$dest"
  changed=1
}

find "$REPO_ROOT/docs" -type f -name '*.md' ! -path "$TARGET_DIR/*" \
  | while IFS= read -r file; do
      case "$file" in
        *prompts/codex/*) continue ;;
        *prompt-docs-summary.md|*prompt-saturation-rubric.md) continue ;;
      esac

      case "$file" in
        *prompts/*|*prompt*|*codex*) move_doc "$file" ;;
      esac
    done

# Second pass: ensure files already inside the target directory follow the naming rules.
find "$TARGET_DIR" -maxdepth 1 -type f -name '*.md' \
  | while IFS= read -r file; do
      base=$(basename "$file")
      stem=${base%.*}
      ext=${base##*.}
      sanitized=$(sanitize_stem "$stem")
      [ -n "$sanitized" ] || sanitized=$stem
      new_path="$TARGET_DIR/$sanitized.$ext"
      if [ "$file" = "$new_path" ]; then
        continue
      fi
      if [ -f "$new_path" ]; then
        if cmp -s "$file" "$new_path"; then
          rm -f "$file"
          changed=1
          continue
        fi
        i=2
        while [ -f "$TARGET_DIR/$sanitized-$i.$ext" ]; do
          i=$((i + 1))
        done
        new_path="$TARGET_DIR/$sanitized-$i.$ext"
      fi
      mv "$file" "$new_path"
      changed=1
    done

if [ "$changed" -eq 0 ]; then
  printf 'Prompt docs already consolidated at %s\n' "$TARGET_DIR"
else
  printf 'Prompt docs consolidated under %s\n' "$TARGET_DIR"
fi
