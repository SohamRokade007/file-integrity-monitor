"""Baseline creation and integrity comparison."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.scanner import scan_directory
from database.db_manager import DatabaseManager


def create_baseline(
    directory: str | Path,
    database: DatabaseManager,
) -> list[dict[str, Any]]:
    root = Path(directory).expanduser().resolve()
    records = scan_directory(root)
    database.replace_baseline(records, str(root))
    return records


def check_integrity(
    directory: str | Path,
    database: DatabaseManager,
) -> dict[str, list[dict[str, Any]]]:
    """Compare the selected directory with its saved baseline."""
    root = Path(directory).expanduser().resolve()
    baseline_root = database.get_baseline_root()
    if baseline_root is None:
        raise ValueError("No baseline exists. Create a baseline before checking.")
    if str(root) != baseline_root:
        raise ValueError(
            "The selected directory differs from the baseline directory. "
            "Select the original directory or create a new baseline."
        )

    current_records = scan_directory(root)
    baseline = database.get_baseline()
    current = {record["path"]: record for record in current_records}

    result: dict[str, list[dict[str, Any]]] = {
        "added": [], "modified": [], "deleted": []
    }

    for path, record in current.items():
        previous = baseline.get(path)
        if previous is None:
            result["added"].append(record)
            database.add_event("ADDED", path, new_hash=record["sha256"])
        elif previous["sha256"] != record["sha256"]:
            changed = {**record, "old_sha256": previous["sha256"]}
            result["modified"].append(changed)
            database.add_event(
                "MODIFIED", path,
                old_hash=previous["sha256"],
                new_hash=record["sha256"],
            )

    for path, previous in baseline.items():
        if path not in current:
            result["deleted"].append({
                "path": path, "sha256": previous["sha256"]
            })
            database.add_event("DELETED", path, old_hash=previous["sha256"])

    return result
