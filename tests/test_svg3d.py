import pytest
import svgwrite
from src import svg3d


def test_clamp_and_shade():
    assert svg3d._clamp(-5) == 0
    assert svg3d._clamp(300) == 255
    assert svg3d._clamp(128) == 128

    lighter = svg3d._shade("#808080", 1.1)
    darker = svg3d._shade("#808080", 0.9)
    assert lighter == "#8c8c8c"
    assert darker == "#737373"


def test_draw_bar_adds_polygons():
    dwg = svgwrite.Drawing()
    svg3d.draw_bar(dwg, 0, 10, 5, "#123456")
    polys = [e for e in dwg.elements if isinstance(e, svgwrite.shapes.Polygon)]
    assert len(polys) == 3
    assert polys[0].points == [(0, 5), (12, 5), (16, 1), (4, 1)]


def test_shade_invalid_color():
    with pytest.raises(ValueError):
        svg3d._shade("123456", 1)
    with pytest.raises(ValueError):
        svg3d._shade("#zzzzzz", 1)
