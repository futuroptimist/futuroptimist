from pathlib import Path


def test_prompt_files_exist():
    required = [
        Path("docs/prompts/codex/automation.md"),
        Path("docs/prompts/codex/cad.md"),
        Path("docs/prompts/codex/ci-fix.md"),
        Path("docs/prompts/codex/cleanup.md"),
        Path("docs/prompts/codex/fuzzing.md"),
        Path("docs/prompts/codex/physics.md"),
        Path("docs/prompts/codex/propagate.md"),
        Path("docs/prompts/codex/spellcheck.md"),
        Path("docs/prompts/codex/video-script.md"),
        Path("docs/prompts/codex/video-script-ideas.md"),
        Path("docs/prompt-docs-summary.md"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    assert not missing, f"Missing prompt files: {missing}"
