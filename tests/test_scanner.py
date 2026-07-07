from pathlib import Path

from repo_insight.config import Settings
from repo_insight.scanner import scan_repository


def test_scan_repository_collects_expected_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\nA small project", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("streamlit==1.41.0", encoding="utf-8")
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.py").write_text("print('hello')", encoding="utf-8")
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "large.js").write_text("ignored", encoding="utf-8")

    snapshot = scan_repository(
        tmp_path, "https://github.com/org/demo.git", "demo", Settings()
    )

    assert snapshot.readme_path == "README.md"
    assert "A small project" in snapshot.readme_content
    assert snapshot.dependency_files == {"requirements.txt": "streamlit==1.41.0"}
    assert snapshot.source_samples == {"src/main.py": "print('hello')"}
    assert "node_modules" not in snapshot.directory_tree
    assert snapshot.total_files == 3


def test_scanner_truncates_large_text_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("x" * 20, encoding="utf-8")
    settings = Settings(max_readme_chars=10)

    snapshot = scan_repository(tmp_path, "https://github.com/org/demo.git", "demo", settings)

    assert snapshot.readme_content.startswith("x" * 10)
    assert "已截断" in snapshot.readme_content


def test_scanner_does_not_read_symlinks_when_supported(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("secret", encoding="utf-8")
    link = tmp_path / "requirements.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        return

    snapshot = scan_repository(tmp_path, "https://github.com/org/demo.git", "demo", Settings())
    assert snapshot.dependency_files == {}

