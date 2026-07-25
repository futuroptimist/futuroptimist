import pathlib
import re


def test_asset_plan_maps_every_cue_and_defines_every_asset_once():
    root = (
        pathlib.Path(__file__).resolve().parents[1]
        / "video_scripts"
        / "20260901_sugarkube"
    )
    master = (root / "footage.md").read_text()
    detail_paths = [
        root / "production" / "broll.md",
        root / "production" / "stock.md",
        root / "production" / "graphics.md",
    ]
    for path in detail_paths:
        assert path.relative_to(root).as_posix() in master

    rows = re.findall(r"^\| (V\d{2}) \|.*?\| ([A-Z0-9, ]+) \|$", master, re.MULTILINE)
    assert [cue for cue, _ in rows] == [f"V{i:02d}" for i in range(1, 43)]
    referenced = {
        asset for _, assets in rows for asset in re.findall(r"[ABCTG]\d{2}", assets)
    }

    definitions = []
    for path in detail_paths:
        definitions.extend(
            re.findall(
                r"^- \[[ x!\-]\] \*\*([ABCTG]\d{2})\*\*", path.read_text(), re.MULTILINE
            )
        )
    assert len(definitions) == len(set(definitions))
    assert referenced <= set(definitions)
