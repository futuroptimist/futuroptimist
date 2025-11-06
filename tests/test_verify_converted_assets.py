from PIL import Image

from src.verify_converted_assets import verify_slug


def test_verify_slug_detects_mismatch(tmp_path):
    slug = tmp_path / "20251001_x"
    (slug / "originals").mkdir(parents=True)
    (slug / "converted").mkdir(parents=True)
    orig = slug / "originals" / "a.webp"
    conv = slug / "converted" / "a.png"
    # 400x300 original, 300x300 converted -> mismatch
    Image.new("RGB", (400, 300), color="red").save(orig, format="WEBP")
    Image.new("RGB", (300, 300), color="red").save(conv)
    errors = verify_slug(slug, tolerance=0.001)
    # With current verifier, identical names in converted are compared; ensure mismatch is flagged
    assert any("Aspect mismatch" in e for e in errors)


def test_verify_slug_pass(tmp_path):
    slug = tmp_path / "20251001_y"
    (slug / "originals").mkdir(parents=True)
    (slug / "converted").mkdir(parents=True)
    orig = slug / "originals" / "b.png"
    conv = slug / "converted" / "b.png"
    Image.new("RGB", (1920, 1080), color="blue").save(orig)
    Image.new("RGB", (1920, 1080), color="blue").save(conv)
    errors = verify_slug(slug)
    assert errors == []
