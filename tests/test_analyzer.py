from pathlib import Path

from repo_insight.analyzer import build_analysis_context
from repo_insight.models import RepositorySnapshot


def _snapshot() -> RepositorySnapshot:
    return RepositorySnapshot(
        url="https://github.com/org/demo.git",
        name="demo",
        root=Path("demo"),
        directory_tree="demo/\n└── app.py",
        readme_path="README.md",
        readme_content="# Demo",
        dependency_files={"requirements.txt": "streamlit"},
        source_samples={"app.py": "print('hello')"},
        total_files=3,
        total_directories=0,
        extension_counts={".py": 1, ".md": 1, ".txt": 1},
    )


def test_analysis_context_contains_repository_facts() -> None:
    context = build_analysis_context(_snapshot(), 10_000)
    assert "https://github.com/org/demo.git" in context
    assert "requirements.txt" in context
    assert "app.py" in context
    assert "# Demo" in context


def test_analysis_context_honors_character_limit() -> None:
    context = build_analysis_context(_snapshot(), 100)
    assert context.endswith("[仓库快照因上下文上限而截断]")
    assert len(context) < 150

