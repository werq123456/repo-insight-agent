from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from repo_insight.git_service import (
    CloneError,
    RepositoryURLError,
    clone_repository,
    normalize_github_url,
)


@pytest.mark.parametrize(
    ("raw", "expected_url", "expected_name"),
    [
        (
            "https://github.com/openai/openai-python",
            "https://github.com/openai/openai-python.git",
            "openai-python",
        ),
        ("https://www.github.com/org/repo.git/", "https://github.com/org/repo.git", "repo"),
    ],
)
def test_normalize_github_url(raw: str, expected_url: str, expected_name: str) -> None:
    assert normalize_github_url(raw) == (expected_url, expected_name)


@pytest.mark.parametrize(
    "raw",
    [
        "http://github.com/org/repo",
        "https://gitlab.com/org/repo",
        "https://github.com/org/repo/issues",
        "https://token@github.com/org/repo",
        "https://github.com/org/repo?tab=readme",
        "not-a-url",
    ],
)
def test_rejects_unsafe_or_non_repository_urls(raw: str) -> None:
    with pytest.raises(RepositoryURLError):
        normalize_github_url(raw)


@patch("repo_insight.git_service.subprocess.run")
def test_clone_uses_argument_list(mock_run: Mock, tmp_path: Path) -> None:
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    destination = tmp_path / "repo"

    clone_repository("https://github.com/org/repo", destination)

    command = mock_run.call_args.args[0]
    assert command[:3] == ["git", "clone", "--depth"]
    assert "--" in command
    assert command[-2:] == ["https://github.com/org/repo.git", str(destination)]


@patch("repo_insight.git_service.subprocess.run")
def test_clone_error_is_readable(mock_run: Mock, tmp_path: Path) -> None:
    mock_run.return_value = Mock(returncode=128, stdout="", stderr="repository not found")
    with pytest.raises(CloneError, match="repository not found"):
        clone_repository("https://github.com/org/repo", tmp_path / "repo")
