import json
import pathlib
import warnings

from src.index_assets import _load_schema


def test_schema_loads():
    schema = _load_schema()
    assert schema["title"] == "AssetsManifest"


def test_build_index_with_labels(tmp_path, monkeypatch):
    # Create a fake repo structure under tmp_path
    repo = tmp_path
    (repo / "schemas").mkdir(parents=True)
    (repo / "video_scripts" / "20251001_indoor-aquariums-tour").mkdir(parents=True)
    (repo / "footage" / "aquaria" / "20250830").mkdir(parents=True)
    # Write schema
    schema_src = pathlib.Path("schemas/assets_manifest.schema.json").read_text()
    (repo / "schemas" / "assets_manifest.schema.json").write_text(schema_src)
    # Write a manifest
    manifest = {
        "footage_dirs": [
            "footage/20251001_indoor-aquariums-tour/originals",
            "footage/20251001_indoor-aquariums-tour/selects",
        ],
        "labels_files": ["footage/20251001_indoor-aquariums-tour/labels.json"],
        "notes_file": "footage/20251001_indoor-aquariums-tour/notes.md",
        "tags": ["aquariums"],
        "capture_date": "2025-08-30",
    }
    mpath = repo / "video_scripts" / "20251001_indoor-aquariums-tour" / "assets.json"
    mpath.write_text(json.dumps(manifest))
    # Make some files
    (repo / "footage" / "20251001_indoor-aquariums-tour" / "originals").mkdir(
        parents=True
    )
    f1 = repo / "footage" / "20251001_indoor-aquariums-tour" / "originals" / "clip1.mp4"
    f1.write_bytes(b"x" * 10)
    f2 = repo / "footage" / "20251001_indoor-aquariums-tour" / "originals" / "img1.jpg"
    f2.write_bytes(b"y" * 5)
    # Labels
    labels = [
        {
            "path": "20251001_indoor-aquariums-tour/originals/clip1.mp4",
            "script_lines": [23, 31],
            "tags": ["in-tank"],
        }
    ]
    (repo / "footage" / "20251001_indoor-aquariums-tour" / "labels.json").write_text(
        json.dumps(labels)
    )

    # Point module to tmp repo by monkeypatching REPO_ROOT
    import src.index_assets as ia

    monkeypatch.setattr(ia, "REPO_ROOT", repo)
    index = ia.build_index()
    paths = [e["path"] for e in index]
    assert "footage/20251001_indoor-aquariums-tour/originals/clip1.mp4" in paths
    assert "footage/20251001_indoor-aquariums-tour/originals/img1.jpg" in paths
    # Match labels association
    labeled = next(e for e in index if e["path"].endswith("clip1.mp4"))
    assert labeled["labels"]["script_lines"] == [23, 31]
    assert labeled["tags"] == ["aquariums"]
    # notes_file should be propagated so downstream tooling can locate shoot notes
    assert labeled["notes_file"] == ("footage/20251001_indoor-aquariums-tour/notes.md")


def test_build_index_normalizes_notes_file(tmp_path, monkeypatch):
    repo = tmp_path
    slug = "20251001_indoor-aquariums-tour"
    (repo / "schemas").mkdir(parents=True)
    (repo / "video_scripts" / slug).mkdir(parents=True)
    (repo / "footage" / slug / "originals").mkdir(parents=True)

    schema_src = pathlib.Path("schemas/assets_manifest.schema.json").read_text()
    (repo / "schemas" / "assets_manifest.schema.json").write_text(schema_src)

    manifest = {
        "footage_dirs": [f"footage/{slug}/originals"],
        "notes_file": "notes.md",
    }
    manifest_path = repo / "video_scripts" / slug / "assets.json"
    manifest_path.write_text(json.dumps(manifest))

    notes_path = repo / "video_scripts" / slug / "notes.md"
    notes_path.write_text("shoot notes")

    # Create an example asset so the index isn't empty
    asset = repo / "footage" / slug / "originals" / "clip.mp4"
    asset.write_bytes(b"x")

    import src.index_assets as ia

    monkeypatch.setattr(ia, "REPO_ROOT", repo)
    index = ia.build_index()
    assert index, "Expected at least one indexed asset"
    for entry in index:
        assert entry["notes_file"] == f"video_scripts/{slug}/notes.md"


def test_entrypoint_runs(tmp_path, monkeypatch):
    repo = tmp_path
    (repo / "schemas").mkdir(parents=True)
    (repo / "video_scripts" / "x").mkdir(parents=True)
    (repo / "footage" / "x").mkdir(parents=True)
    schema_src = pathlib.Path("schemas/assets_manifest.schema.json").read_text()
    (repo / "schemas" / "assets_manifest.schema.json").write_text(schema_src)
    (repo / "video_scripts" / "x" / "assets.json").write_text(
        json.dumps({"footage_dirs": ["footage/x"]})
    )
    f = repo / "footage" / "x" / "a.mov"
    f.write_text("a")
    out = repo / "assets_index.json"
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PYTHONPATH", str(repo))
    import src.index_assets as ia

    monkeypatch.setattr(ia, "REPO_ROOT", repo)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        ia.main(["-o", str(out)])
    assert out.exists()
    data = json.loads(out.read_text())
    assert any(e["path"].endswith("a.mov") for e in data)
