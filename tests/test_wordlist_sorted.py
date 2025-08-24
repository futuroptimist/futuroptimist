from pathlib import Path


def test_wordlist_is_alphabetized():
    """Ensure .wordlist.txt entries remain alphabetically sorted."""
    wordlist_path = Path(__file__).resolve().parent.parent / ".wordlist.txt"
    with wordlist_path.open(encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    assert words == sorted(words), ".wordlist.txt is not alphabetically sorted"
