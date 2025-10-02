import subprocess
import pathlib
import sys
import shutil

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
IDS_FILE = BASE_DIR / "video_ids.txt"
OUTPUT_DIR = BASE_DIR / "subtitles"


def _normalize_vtt_timestamp(raw: str) -> str:
    token = raw.strip()
    sep = "." if "." in token else ","
    if sep in token:
        base, frac = token.split(sep, 1)
    else:
        base, frac = token, "000"
    parts = base.split(":")
    if len(parts) == 2:
        base = f"00:{parts[0]}:{parts[1]}"
    elif len(parts) == 1:
        base = f"00:00:{parts[0]}"
    frac = (frac + "000")[:3]
    return f"{base},{frac}"


def _iter_vtt_cues(text: str) -> list[tuple[str, str, list[str]]]:
    cues: list[list[str]] = []
    block: list[str] = []
    skip_meta = False
    for raw_line in text.splitlines():
        line = raw_line.strip("\ufeff")
        stripped = line.strip()
        if skip_meta:
            if stripped == "":
                skip_meta = False
            continue
        upper = stripped.upper()
        if not block and upper.startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            if upper.startswith(("NOTE", "STYLE", "REGION")):
                skip_meta = True
            continue
        if stripped == "":
            if block:
                cues.append(block)
                block = []
            continue
        block.append(line)
    if block:
        cues.append(block)

    parsed: list[tuple[str, str, list[str]]] = []
    for cue in cues:
        time_index = (
            0 if "-->" in cue[0] else 1 if len(cue) > 1 and "-->" in cue[1] else -1
        )
        if time_index == -1:
            continue
        time_line = cue[time_index]
        parts = time_line.split("-->", 1)
        if len(parts) != 2:
            continue
        start_raw, end_raw = parts[0], parts[1]
        end_token = end_raw.strip().split()
        if not end_token:
            continue
        start = _normalize_vtt_timestamp(start_raw)
        end = _normalize_vtt_timestamp(end_token[0])
        text_lines = cue[time_index + 1 :]
        parsed.append((start, end, text_lines))
    return parsed


def _convert_vtt_candidates(video_id: str) -> pathlib.Path | None:
    candidates = sorted(OUTPUT_DIR.glob(f"{video_id}*.vtt"))
    if not candidates:
        return None
    for candidate in candidates:
        try:
            cues = _iter_vtt_cues(candidate.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not cues:
            continue
        lines: list[str] = []
        for idx, (start, end, texts) in enumerate(cues, start=1):
            lines.append(str(idx))
            lines.append(f"{start} --> {end}")
            lines.extend(texts)
            lines.append("")
        srt_path = OUTPUT_DIR / f"{video_id}.srt"
        srt_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        for extra in candidates:
            try:
                extra.unlink(missing_ok=True)
            except TypeError:
                if extra.exists():
                    extra.unlink()
        return srt_path
    return None


def ensure_requirements():
    """Check that yt-dlp is installed."""
    if shutil.which("yt-dlp") is None:
        sys.stderr.write(
            "yt-dlp executable not found in PATH. Install via uv: uv pip install yt-dlp\n"
        )
        sys.exit(1)


def read_video_ids():
    if not IDS_FILE.exists():
        sys.stderr.write(f"IDs file {IDS_FILE} not found.\n")
        sys.exit(1)
    ids = []
    for line in IDS_FILE.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            ids.append(stripped)
    return ids


def download_subtitles(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    # --skip-download avoids video download; --write-sub fetches manual captions only.
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-sub",
        "--sub-lang",
        "en.*",
        "--convert-subs",
        "srt",
        "-o",
        str(OUTPUT_DIR / "%(id)s.%(ext)s"),
        url,
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(
            "Primary download failed – retrying without SRT conversion (raw .vtt will be kept)"
        )
        cmd_fallback = [
            "yt-dlp",
            "--skip-download",
            "--write-sub",
            "--sub-lang",
            "en.*",
            "-o",
            str(OUTPUT_DIR / "%(id)s.%(ext)s"),
            url,
        ]
        subprocess.run(cmd_fallback, check=True)
        if not (OUTPUT_DIR / f"{video_id}.srt").exists():
            converted = _convert_vtt_candidates(video_id)
            if not converted:
                print(
                    f"Unable to convert VTT subtitles for {video_id}", file=sys.stderr
                )


def main():
    ensure_requirements()
    OUTPUT_DIR.mkdir(exist_ok=True)
    ids = read_video_ids()
    for vid in ids:
        try:
            print(f"Downloading subtitles for {vid}...")
            download_subtitles(vid)
        except subprocess.CalledProcessError as e:
            print(f"Failed for {vid}: {e}")


if __name__ == "__main__":
    main()
