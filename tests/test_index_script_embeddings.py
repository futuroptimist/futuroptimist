import json
from pathlib import Path

import pytest

import src.index_script_embeddings as embeddings
import src.index_script_segments as segments


@pytest.fixture()
def demo_segments(tmp_path: Path) -> Path:
    video_root = tmp_path / "video_scripts"
    slug_dir = video_root / "20240229_demo"
    slug_dir.mkdir(parents=True, exist_ok=True)
    (slug_dir / "metadata.json").write_text(
        json.dumps(
            {
                "youtube_id": "XYZ789",
                "title": "Leap Day Lab",
                "publish_date": "2024-02-29",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (slug_dir / "script.md").write_text(
        "\n".join(
            [
                "# Leap Day Lab",
                "",
                "> Outline for leap day experiment",
                "",
                "## Script",
                "",
                "[NARRATOR]: First discovery.",
                "",
                "[VISUAL]: Microscope b-roll",
                "",
                "[NARRATOR]: Second discovery with more detail.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    segments_path = tmp_path / "segments.json"
    segments.build_index(video_root=video_root, output_path=segments_path)
    return segments_path


def test_build_embeddings_writes_vectors(tmp_path: Path, demo_segments: Path) -> None:
    output_path = tmp_path / "embeddings.json"
    payload = embeddings.build_embeddings(
        segments_path=demo_segments, output_path=output_path, dimensions=8
    )

    assert output_path.exists()
    assert payload == json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["dimensions"] == 8
    assert payload["model"].startswith("hash-")
    assert payload["generated_at"].endswith("Z")

    vectors = payload["segments"]
    assert len(vectors) == 2
    first = vectors[0]
    assert first["slug"] == "20240229_demo"
    assert len(first["embedding"]) == 8
    assert first["embedding"] == [
        0.384477,
        0.399095,
        0.086093,
        0.483507,
        -0.75145,
        -0.326835,
        -0.648899,
        0.801693,
    ]


def test_main_cli_creates_index(tmp_path: Path, demo_segments: Path) -> None:
    output_path = tmp_path / "cli.json"
    exit_code = embeddings.main(
        [
            "--segments",
            str(demo_segments),
            "--output",
            str(output_path),
            "--dimensions",
            "6",
        ]
    )

    assert exit_code == 0
    content = json.loads(output_path.read_text(encoding="utf-8"))
    assert content["dimensions"] == 6
    assert content["segments"][0]["embedding"]
