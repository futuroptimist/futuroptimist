import pathlib

from src.describe_images import is_image, describe_images


def test_is_image_detection():
    assert is_image(pathlib.Path("a.jpg"))
    assert is_image(pathlib.Path("b.PNG"))
    assert is_image(pathlib.Path("c.heic"))
    assert not is_image(pathlib.Path("d.mp4"))


def test_describe_images_collects(tmp_path):
    img = tmp_path / "x.jpg"
    img.write_bytes(b"1234")
    vid = tmp_path / "y.mp4"
    vid.write_bytes(b"zz")
    entries = describe_images(tmp_path)
    paths = [e["path"] for e in entries]
    assert img.as_posix() in paths
    assert all(".mp4" not in p for p in paths)
