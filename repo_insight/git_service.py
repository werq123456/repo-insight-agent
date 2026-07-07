"""Safe GitHub URL validation and shallow cloning."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


class RepositoryURLError(ValueError):
    """Raised when a repository URL is not an accepted GitHub HTTPS URL."""


class CloneError(RuntimeError):
    """Raised when Git cannot clone a repository."""


_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def normalize_github_url(raw_url: str) -> tuple[str, str]:
    """Validate a public GitHub HTTPS repository URL and return URL and repo name."""

    value = raw_url.strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise RepositoryURLError("请输入 https://github.com/owner/repository 格式的 GitHub URL。")
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        raise RepositoryURLError("仓库 URL 不能包含凭据、端口、查询参数或片段。")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise RepositoryURLError("仓库 URL 必须只包含 owner 和 repository 两段路径。")

    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    valid_segments = _SEGMENT_RE.fullmatch(owner) and _SEGMENT_RE.fullmatch(repository)
    if not owner or not repository or not valid_segments:
        raise RepositoryURLError("GitHub owner 或仓库名包含不支持的字符。")

    return f"https://github.com/{owner}/{repository}.git", repository


def clone_repository(
    raw_url: str, destination: Path, timeout_seconds: int = 180
) -> tuple[str, str]:
    """Shallow-clone a repository into a destination that does not yet exist."""

    normalized_url, repository_name = normalize_github_url(raw_url)
    if destination.exists():
        raise CloneError(f"目标目录已存在：{destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--quiet",
        "--",
        normalized_url,
        str(destination),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CloneError("未找到 Git，请先安装 Git 并确保 git 命令在 PATH 中。") from exc
    except subprocess.TimeoutExpired as exc:
        raise CloneError(f"克隆超时（{timeout_seconds} 秒），仓库可能过大或网络较慢。") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "未知 Git 错误").strip()
        raise CloneError(f"克隆失败：{detail[-1200:]}")

    return normalized_url, repository_name
