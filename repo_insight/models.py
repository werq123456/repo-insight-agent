"""Data models shared across the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RepositorySnapshot:
    """A bounded, text-only view of a cloned repository."""

    url: str
    name: str
    root: Path
    directory_tree: str
    readme_path: str | None = None
    readme_content: str = ""
    dependency_files: dict[str, str] = field(default_factory=dict)
    source_samples: dict[str, str] = field(default_factory=dict)
    total_files: int = 0
    total_directories: int = 0
    extension_counts: dict[str, int] = field(default_factory=dict)
    truncated_tree: bool = False

