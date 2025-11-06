from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw


@pytest.fixture(name="thumbnail_paths")
def _thumbnail_paths(tmp_path: Path) -> dict[str, Path]:
    bright = tmp_path / "bright.png"
    dull = tmp_path / "dull.png"

    bright_image = Image.new("RGB", (400, 225), color=(252, 210, 60))
    bright_draw = ImageDraw.Draw(bright_image)
    bright_draw.rectangle((30, 60, 370, 140), fill=(20, 20, 20))
    bright_image.save(bright)

    dull_image = Image.new("RGB", (400, 225), color=(140, 140, 140))
    dull_draw = ImageDraw.Draw(dull_image)
    dull_draw.rectangle((30, 60, 370, 140), fill=(120, 120, 120))
    dull_image.save(dull)

    return {"bright": bright, "dull": dull}


def test_predict_ctr_rewards_concise_high_contrast(
    thumbnail_paths: dict[str, Path],
) -> None:
    from src import thumbnail_text_predictor as predictor

    prediction = predictor.predict_ctr(thumbnail_paths["bright"], "Build Solar Farm")
    assert 0.6 < prediction.score < 1.0
    assert any("Concise text" in reason for reason in prediction.reasons)
    assert any("High contrast" in reason for reason in prediction.reasons)


def test_predict_ctr_penalizes_long_busy_text(thumbnail_paths: dict[str, Path]) -> None:
    from src import thumbnail_text_predictor as predictor

    busy_text = "10 unbelievable DIY automation tricks you must try now!!!"
    prediction = predictor.predict_ctr(thumbnail_paths["dull"], busy_text)
    assert 0 <= prediction.score < 0.4
    assert any("Text is lengthy" in reason for reason in prediction.reasons)
    assert any("Multiple punctuation" in reason for reason in prediction.reasons)
