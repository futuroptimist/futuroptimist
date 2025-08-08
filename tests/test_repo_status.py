from src.repo_status import status_to_emoji


def test_status_to_emoji() -> None:
    assert status_to_emoji("success") == "✅"
    assert status_to_emoji("failure") == "❌"
    assert status_to_emoji(None) == "❌"
