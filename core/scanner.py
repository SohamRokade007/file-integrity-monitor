"""Directory scanner that produces SHA-256 file records."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.hasher import calculate_sha256


def scan_directory(directory: str | Path) -> list[dict[str, Any]]:
    """Hash regular files below a directory; do not follow symbolic links."""
    root = Path(directory).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    records: list[dict[str, Any]] = []
    for current, dirs, filenames in os.walk(root, followlinks=False):
        dirs[:] = [
            name for name in dirs
            if not (Path(current) / name).is_symlink()
        ]
        for filename in filenames:
            path = Path(current) / filename
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                stat = path.stat()
                records.append({
                    "path": path.relative_to(root).as_posix(),
                    "absolute_path": str(path),
                    "sha256": calculate_sha256(path),
                    "size": stat.st_size,
                    "modified_ns": stat.st_mtime_ns,
                })
            except FileNotFoundError:
                # The file may have disappeared between enumeration and hashing.
                continue
            except PermissionError as exc:
                # Do not silently skip unreadable files: that could look like deletion.
                raise PermissionError(f"Cannot read {path}: {exc}") from exc

    return sorted(records, key=lambda record: record["path"].casefold())
