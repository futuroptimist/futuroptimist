import pathlib

from PIL import Image

from src.describe_images import describe_images, is_image


def test_is_image_detection():
    assert is_image(pathlib.Path("a.jpg"))
    assert is_image(pathlib.Path("b.PNG"))
    assert is_image(pathlib.Path("c.heic"))
    assert not is_image(pathlib.Path("d.mp4"))


def test_describe_images_generates_summary(tmp_path):
    img = tmp_path / "x.png"
    Image.new("RGB", (40, 20), color=(240, 120, 10)).save(img)

    vid = tmp_path / "y.mp4"
    vid.write_bytes(b"zz")

    entries = describe_images(tmp_path)
    paths = [entry["path"] for entry in entries]
    record = {entry["path"]: entry for entry in entries}[img.as_posix()]
    description = record["description"].lower()

    assert "landscape" in description
    assert "png" in description
    assert "40x20" in description
    assert "pending" not in description
    assert all(not p.endswith(".mp4") for p in paths)
