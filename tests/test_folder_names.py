import pathlib
import re


def test_script_folder_naming():
    pattern = re.compile(r"^\d{8}_[a-z0-9\-]+$")
    for p in pathlib.Path("video_scripts").iterdir():
        if p.is_dir() and p.name != "__pycache__":
            assert pattern.match(
                p.name
            ), f"Folder {p.name} does not match YYYYMMDD_slug convention"
