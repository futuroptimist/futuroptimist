#!/usr/bin/env bash
set -euo pipefail

pre-commit run --all-files
pytest -q

if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
  npm run lint
  npm run docs-lint
  npm run test:ci
else
  echo "Skipping npm checks: package.json not found or npm missing" >&2
fi

