"""Optional real-time filesystem change notifications."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str, str], None]) -> None:
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if event.event_type not in {"created", "modified", "deleted", "moved"}:
            return

        self.callback(event.event_type.upper(), str(event.src_path))
        destination = getattr(event, "dest_path", None)
        if event.event_type == "moved" and destination:
            self.callback("MOVED_TO", str(destination))


def start_monitor(
    directory: str | Path,
    callback: Callable[[str, str], None],
) -> Observer:
    """Start a recursive watcher. Stop and join the returned observer on shutdown."""
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    observer = Observer()
    observer.schedule(_ChangeHandler(callback), str(root), recursive=True)
    observer.start()
    return observer
