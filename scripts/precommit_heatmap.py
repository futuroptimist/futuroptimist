"""Run the heatmap generator if available, otherwise exit cleanly."""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    spec = importlib.util.find_spec("src.generate_heatmap")
    if spec is None:
        sys.stderr.write("Skipping heatmap: src.generate_heatmap not found\n")
        return 0
    module = importlib.import_module("src.generate_heatmap")
    if hasattr(module, "main"):
        result = module.main()  # type: ignore[call-arg]
        return int(result or 0)
    runpy.run_module("src.generate_heatmap", run_name="__main__")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
