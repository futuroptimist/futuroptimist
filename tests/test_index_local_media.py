import json
import scripts.index_local_media as ilm


def test_scan_directory(tmp_path):
    (tmp_path / "dir").mkdir()
    f1 = tmp_path / "dir" / "a.jpg"
    f1.write_text("a")
    f2 = tmp_path / "b.mp4"
    f2.write_text("b")
    result = ilm.scan_directory(tmp_path)
    names = {r["path"] for r in result}
    assert names == {"dir/a.jpg", "b.mp4"}


def test_main(tmp_path, capsys):
    f = tmp_path / "x.txt"
    f.write_text("hi")
    out_file = tmp_path / "index.json"
    ilm.main([str(tmp_path), "-o", str(out_file)])
    captured = capsys.readouterr()
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data[0]["path"] == "x.txt"
    assert "Wrote" in captured.out
