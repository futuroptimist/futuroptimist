import re
from pathlib import Path


def test_production_coverage_and_asset_definitions():
    root = Path("video_scripts/20260901_sugarkube")
    master = (root / "footage.md").read_text()
    details = ["production/broll.md", "production/stock.md", "production/graphics.md"]
    assert all(f"]({path})" in master for path in details)
    cues = re.findall(r"^\| (V\d{2}) \|", master, re.MULTILINE)
    assert cues == [f"V{i:02}" for i in range(1, 43)]
    definitions = []
    for relative in details:
        definitions += re.findall(
            r"^- \[.\] \*\*([ABCTG]\d{2})\*\*",
            (root / relative).read_text(),
            re.MULTILINE,
        )
    assert len(definitions) == len(set(definitions))
    references = set(re.findall(r"`([ABCTG]\d{2})`", master))
    assert references == set(definitions)
