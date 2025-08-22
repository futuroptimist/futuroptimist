from pathlib import Path


def test_heatmap_workflow_sets_up_uv():
    content = Path(".github/workflows/contrib-heatmap.yml").read_text()
    assert "astral-sh/setup-uv@v1" in content
