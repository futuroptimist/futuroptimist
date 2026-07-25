import pathlib
import re


def test_coverage_and_asset_definitions():
    root = pathlib.Path("video_scripts/20260901_sugarkube")
    master = (root / "footage.md").read_text()
    details = [
        root / "production" / name for name in ("broll.md", "stock.md", "graphics.md")
    ]
    rows = re.findall(r"^\| (V\d{2}) \| ([A-Z]\d{2}(?: [A-Z]\d{2})*) \|$", master, re.M)
    assert [cue for cue, _ in rows] == [f"V{i:02}" for i in range(1, 43)]
    definitions = re.findall(
        r"^\- \[ \] \*\*([ABCTG]\d{2})\*\*",
        "\n".join(path.read_text() for path in details),
        re.M,
    )
    assert len(definitions) == len(set(definitions))
    referenced = {asset for _, assets in rows for asset in assets.split()}
    assert referenced <= set(definitions)
    for path in details:
        assert f"production/{path.name}" in master
