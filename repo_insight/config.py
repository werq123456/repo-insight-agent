"""Application configuration and scanning limits."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings, overridable through environment variables."""

    default_model: str = "qwen3.7-plus"
    api_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    clone_timeout_seconds: int = 180
    max_tree_depth: int = 5
    max_tree_entries: int = 500
    max_readme_chars: int = 30_000
    max_dependency_chars_per_file: int = 12_000
    max_source_files: int = 12
    max_source_chars_per_file: int = 6_000
    max_context_chars: int = 90_000

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            default_model=os.getenv("QWEN_MODEL", cls.default_model),
            api_base_url=os.getenv("DASHSCOPE_BASE_URL", cls.api_base_url),
            clone_timeout_seconds=int(
                os.getenv("CLONE_TIMEOUT_SECONDS", cls.clone_timeout_seconds)
            ),
        )


IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "target",
        "coverage",
        ".next",
        ".nuxt",
        ".cache",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
    }
)

DEPENDENCY_FILENAMES = frozenset(
    {
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "poetry.lock",
        "pdm.lock",
        "pipfile",
        "pipfile.lock",
        "setup.py",
        "setup.cfg",
        "environment.yml",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lock",
        "bun.lockb",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
        "gemfile",
        "gemfile.lock",
        "composer.json",
        "composer.lock",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "gradle.properties",
        "mix.exs",
        "pubspec.yaml",
        "packages.config",
        "project.clj",
    }
)

SOURCE_EXTENSIONS = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".cs",
        ".cpp",
        ".cc",
        ".c",
        ".h",
        ".hpp",
        ".swift",
        ".kt",
        ".kts",
        ".scala",
        ".vue",
        ".svelte",
        ".dart",
        ".ex",
        ".exs",
        ".sh",
        ".sql",
    }
)
