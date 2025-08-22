#!/usr/bin/env bash
set -euo pipefail

pre-commit run --all-files
pytest -q

if [ -f package.json ]; then
  npm run lint
  npm run test:ci
else
  echo "Skipping npm checks: package.json not found" >&2
fi

if python - <<'PY'
import pkgutil
import sys
sys.exit(0 if pkgutil.find_loader('flywheel') else 1)
PY
then
  python -m flywheel.fit
else
  echo "Skipping flywheel.fit: module not found" >&2
fi
