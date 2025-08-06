import runpy
from pathlib import Path


def test_heatmap_modules_importable_as_scripts():
    base = Path(__file__).resolve().parent.parent / "src"
    runpy.run_path(base / "gh_graphql.py")
    runpy.run_path(base / "gh_rest.py")
