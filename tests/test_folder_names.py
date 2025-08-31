import pathlib
import re


def test_script_folder_naming():
    final_pattern = re.compile(r"^\d{8}_[a-z0-9\-]+$")
    draft_pattern = re.compile(r"^[a-z0-9\-]+$")
    for p in pathlib.Path("video_scripts").iterdir():
        if p.is_dir() and p.name != "__pycache__":
            if p.name == "drafts":
                for d in p.iterdir():
                    if d.is_dir():
                        assert draft_pattern.match(
                            d.name
                        ), f"Draft folder {d.name} should be slug-only"
            else:
                assert final_pattern.match(
                    p.name
                ), f"Folder {p.name} does not match YYYYMMDD_slug convention"
                # If a matching footage directory exists, enforce same top-level name
                footage_dir = pathlib.Path("footage") / p.name
                if footage_dir.exists():
                    assert (
                        footage_dir.is_dir()
                    ), f"Footage path {footage_dir} should be a directory"
