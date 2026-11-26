"""Knowledge of a concrete backend stays in its module and the command line."""

from pathlib import Path

SOURCE = Path(__file__).parents[1] / "src" / "agent_pfc"
MAY_NAME_OLLAMA = {Path("embeddings/ollama.py"), Path("cli.py")}


def test_only_the_backend_and_command_line_mention_ollama() -> None:
    files = [path.relative_to(SOURCE) for path in sorted(SOURCE.rglob("*.py"))]
    assert Path("embeddings/ollama.py") in files
    mentions = [
        str(path)
        for path in files
        if path not in MAY_NAME_OLLAMA
        and any(
            word in (SOURCE / path).read_text().lower()
            for word in ("ollama", "11434", "/api/embed")
        )
    ]
    assert mentions == []
