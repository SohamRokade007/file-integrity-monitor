"""Background periodic integrity checks."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from core.integrity import check_integrity
from database.db_manager import DatabaseManager


class PeriodicMonitor:
    def __init__(
        self,
        directory: str | Path,
        database: DatabaseManager,
        interval_seconds: int = 60,
    ) -> None:
        if interval_seconds < 5:
            raise ValueError("Periodic interval must be at least 5 seconds.")
        self.directory = Path(directory).expanduser().resolve()
        self.database = database
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="fim-periodic-monitor", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            try:
                result = check_integrity(self.directory, self.database)
                logging.info(
                    "Periodic check: %d added, %d modified, %d deleted",
                    len(result["added"]),
                    len(result["modified"]),
                    len(result["deleted"]),
                )
            except Exception:
                logging.exception("Periodic integrity check failed")
