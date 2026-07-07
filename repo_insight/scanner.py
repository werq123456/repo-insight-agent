"""Repository filesystem scanner with bounded reads."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from .config import DEPENDENCY_FILENAMES, IGNORED_DIRECTORIES, SOURCE_EXTENSIONS, Settings
from .models import RepositorySnapshot

README_NAMES = ("readme.md", "readme.rst", "readme.txt", "readme")
ENTRYPOINT_NAMES = frozenset(
    {
        "main.py",
        "app.py",
        "server.py",
        "cli.py",
        "index.js",
        "index.ts",
        "main.js",
        "main.ts",
        "app.js",
        "app.ts",
        "main.go",
        "main.rs",
        "program.cs",
    }
)


def _is_inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _read_text(path: Path, root: Path, max_chars: int) -> str:
    """Read a regular non-symlink file without escaping the repository root."""

    if path.is_symlink() or not path.is_file() or not _is_inside_root(path, root):
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as file:
            content = file.read(max_chars + 1)
    except OSError:
        return ""
    if len(content) > max_chars:
        return content[:max_chars] + "\n\n[内容已截断]"
    return content


def _walk_files(root: Path) -> tuple[list[Path], int]:
    files: list[Path] = []
    directory_count = 0
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
            and not (Path(current) / directory).is_symlink()
        )
        directory_count += len(directories)
        for filename in sorted(filenames):
            path = Path(current) / filename
            if not path.is_symlink():
                files.append(path)
    return files, directory_count


def build_directory_tree(root: Path, max_depth: int, max_entries: int) -> tuple[str, bool]:
    """Build a compact, deterministic tree representation."""

    lines = [f"{root.name}/"]
    entries_seen = 0
    truncated = False

    def visit(directory: Path, prefix: str, depth: int) -> None:
        nonlocal entries_seen, truncated
        if depth > max_depth or entries_seen >= max_entries:
            truncated = True
            return
        try:
            children = [
                child
                for child in directory.iterdir()
                if child.name not in IGNORED_DIRECTORIES and not child.is_symlink()
            ]
        except OSError:
            return
        children.sort(key=lambda item: (not item.is_dir(), item.name.lower()))
        for index, child in enumerate(children):
            if entries_seen >= max_entries:
                lines.append(f"{prefix}└── …（目录树已截断）")
                truncated = True
                return
            is_last = index == len(children) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{prefix}{connector}{child.name}{suffix}")
            entries_seen += 1
            if child.is_dir():
                if depth < max_depth:
                    visit(child, prefix + ("    " if is_last else "│   "), depth + 1)
                else:
                    try:
                        if any(child.iterdir()):
                            lines.append(prefix + ("    " if is_last else "│   ") + "└── …")
                            truncated = True
                    except OSError:
                        pass

    visit(root, "", 1)
    return "\n".join(lines), truncated


def _find_readme(files: list[Path], root: Path) -> Path | None:
    candidates = [path for path in files if path.name.lower() in README_NAMES]
    if not candidates:
        return None
    return min(candidates, key=lambda path: (len(path.relative_to(root).parts), str(path).lower()))


def _source_priority(path: Path, root: Path) -> tuple[int, int, str]:
    relative = path.relative_to(root)
    name = path.name.lower()
    entrypoint_rank = 0 if name in ENTRYPOINT_NAMES else 1
    return entrypoint_rank, len(relative.parts), relative.as_posix().lower()


def scan_repository(root: Path, url: str, name: str, settings: Settings) -> RepositorySnapshot:
    """Collect the repository facts needed by the UI and the language model."""

    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"仓库目录不存在：{root}")

    files, directory_count = _walk_files(root)
    tree, truncated_tree = build_directory_tree(
        root, settings.max_tree_depth, settings.max_tree_entries
    )

    readme_path = _find_readme(files, root)
    readme_content = (
        _read_text(readme_path, root, settings.max_readme_chars) if readme_path else ""
    )

    dependency_files: dict[str, str] = {}
    for path in files:
        lower_name = path.name.lower()
        is_requirements_variant = lower_name.startswith("requirements") and lower_name.endswith(
            ".txt"
        )
        if lower_name in DEPENDENCY_FILENAMES or is_requirements_variant:
            relative = path.relative_to(root).as_posix()
            dependency_files[relative] = _read_text(
                path, root, settings.max_dependency_chars_per_file
            )

    source_candidates = [path for path in files if path.suffix.lower() in SOURCE_EXTENSIONS]
    source_candidates.sort(key=lambda path: _source_priority(path, root))
    source_samples: dict[str, str] = {}
    for path in source_candidates[: settings.max_source_files]:
        content = _read_text(path, root, settings.max_source_chars_per_file)
        if content:
            source_samples[path.relative_to(root).as_posix()] = content

    extension_counts = Counter(path.suffix.lower() or "[无扩展名]" for path in files)
    return RepositorySnapshot(
        url=url,
        name=name,
        root=root,
        directory_tree=tree,
        readme_path=readme_path.relative_to(root).as_posix() if readme_path else None,
        readme_content=readme_content,
        dependency_files=dependency_files,
        source_samples=source_samples,
        total_files=len(files),
        total_directories=directory_count,
        extension_counts=dict(extension_counts.most_common()),
        truncated_tree=truncated_tree,
    )
