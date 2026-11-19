"""SQLite storage for file baselines and detected events."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("data/fim.db")


class DatabaseManager:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS baseline (
                    path TEXT PRIMARY KEY,
                    sha256 TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified_ns INTEGER NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS baseline_info (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    root_path TEXT NOT NULL,
                    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    old_hash TEXT,
                    new_hash TEXT,
                    details TEXT,
                    detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def replace_baseline(self, records: list[dict[str, Any]], root_path: str) -> None:
        """Atomically replace all baseline records and remember their directory."""
        with self._connect() as connection:
            connection.execute("DELETE FROM baseline")
            connection.executemany(
                """INSERT INTO baseline(path, sha256, size, modified_ns)
                   VALUES (?, ?, ?, ?)""",
                [
                    (r["path"], r["sha256"], r["size"], r["modified_ns"])
                    for r in records
                ],
            )
            connection.execute(
                """INSERT INTO baseline_info(id, root_path, captured_at)
                   VALUES (1, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                     root_path=excluded.root_path,
                     captured_at=CURRENT_TIMESTAMP""",
                (root_path,),
            )

    def get_baseline(self) -> dict[str, dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM baseline").fetchall()
        return {row["path"]: dict(row) for row in rows}

    def get_baseline_root(self) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT root_path FROM baseline_info WHERE id=1"
            ).fetchone()
        return row["root_path"] if row else None

    def add_event(
        self,
        event_type: str,
        path: str,
        old_hash: str | None = None,
        new_hash: str | None = None,
        details: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO events(event_type, path, old_hash, new_hash, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (event_type, path, old_hash, new_hash, details),
            )

    def get_events(self, limit: int = 500) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]
