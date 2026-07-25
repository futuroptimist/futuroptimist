import re
from pathlib import Path


def test_sugarkube_production_asset_coverage() -> None:
    root = Path(__file__).resolve().parents[1] / "video_scripts/20260901_sugarkube"
    footage = (root / "footage.md").read_text()
    detail_paths = [
        root / "production/broll.md",
        root / "production/stock.md",
        root / "production/graphics.md",
    ]
    for path in detail_paths:
        assert f"production/{path.name}" in footage
    mapped = re.findall(r"^\| (V\d{2}) \| ([A-Z0-9, ]+) \|", footage, re.MULTILINE)
    assert [cue for cue, _ in mapped] == [f"V{i:02}" for i in range(1, 43)]
    definitions = []
    for path in detail_paths:
        definitions.extend(
            re.findall(
                r"^- \[[ x!\-]\] \*\*([ABCTG]\d{2})\*\* —",
                path.read_text(),
                re.MULTILINE,
            )
        )
    assert len(definitions) == len(set(definitions))
    references = {
        asset for _, assets in mapped for asset in re.findall(r"[ABCTG]\d{2}", assets)
    }
    assert references <= set(definitions)
