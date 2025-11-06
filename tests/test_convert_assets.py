from src.convert_assets import (
    EXTENSION_RULES,
    build_ffmpeg_cmd,
    find_slug_root,
    plan_conversions,
)


def test_find_slug_root_strips_originals(tmp_path):
    root = tmp_path / "footage"
    p = root / "20251001_indoor-aquariums-tour" / "originals" / "IMG_0001.HEIC"
    p.parent.mkdir(parents=True)
    p.write_text("x")
    slug, rel = find_slug_root(p, root)
    assert slug.name == "20251001_indoor-aquariums-tour"
    assert rel.as_posix() == "IMG_0001.HEIC"


def test_plan_conversions_maps_exts(tmp_path):
    root = tmp_path / "footage" / "20251001_indoor-aquariums-tour" / "originals"
    root.mkdir(parents=True)
    heic = root / "a.HEIC"
    heic.write_text("x")
    webp = root / "b.webp"
    webp.write_text("x")
    convs = plan_conversions(tmp_path / "footage")
    paths = {c.dst.suffix for c in convs}
    assert ".jpg" in paths


def test_plan_conversions_limits_to_sources(tmp_path):
    footage = tmp_path / "footage"
    a_dir = footage / "20250101_alpha" / "originals"
    b_dir = footage / "20250102_beta" / "originals"
    a_dir.mkdir(parents=True)
    b_dir.mkdir(parents=True)
    target = a_dir / "keep.heic"
    target.write_text("x")
    other = b_dir / "skip.heic"
    other.write_text("x")

    convs = plan_conversions(
        footage,
        only_sources={target.resolve()},
    )

    assert [c.src for c in convs] == [target]


def test_build_ffmpeg_cmd_contains_flags(tmp_path):
    src = tmp_path / "x.heic"
    dst = tmp_path / "out.jpg"
    src.write_text("x")
    rule = EXTENSION_RULES[".heic"][1]
    from src.convert_assets import Conversion

    c = Conversion(src=src, dst=dst, extra_args=rule)
    cmd = build_ffmpeg_cmd(c, overwrite=False)
    assert "ffmpeg" in cmd[0].lower()
    assert "-n" in cmd and "-i" in cmd
