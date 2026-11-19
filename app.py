"""Streamlit dashboard for the File Integrity Monitoring System."""
from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from core.integrity import check_integrity, create_baseline
from core.monitor import start_monitor
from core.scheduler import PeriodicMonitor
from database.db_manager import DatabaseManager
from utils.logger import configure_logging

st.set_page_config(page_title="File Integrity Monitor", page_icon="🛡️", layout="wide")
configure_logging()


@st.cache_resource
def get_database() -> DatabaseManager:
    return DatabaseManager()


db = get_database()
st.title("🛡️ File Integrity Monitoring System")
st.caption("SHA-256 based file monitoring with SQLite history, live alerts and periodic checks.")

if "observer" not in st.session_state:
    st.session_state.observer = None
if "periodic_monitor" not in st.session_state:
    st.session_state.periodic_monitor = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None


def validate_directory(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Directory does not exist: {root}")
    db_path = db.db_path.expanduser().resolve()
    if db_path == root or root in db_path.parents:
        raise ValueError(
            "The SQLite database is inside the selected directory. "
            "Choose a separate folder so the database does not monitor itself."
        )
    return root


with st.sidebar:
    st.header("Monitoring setup")
    folder = st.text_input("Directory to monitor", value="monitored_files")
    st.caption("Start with the included monitored_files folder. Avoid system folders.")
    st.divider()

    if st.button("Create / Replace Baseline", type="primary", use_container_width=True):
        try:
            root = validate_directory(folder)
            records = create_baseline(root, db)
            st.session_state.last_result = None
            logging.info("Baseline created for %s with %d files", root, len(records))
            st.success(f"Baseline saved for {len(records)} files.")
        except (OSError, ValueError) as exc:
            st.error(str(exc))

    if st.button("Run Integrity Check", use_container_width=True):
        try:
            root = validate_directory(folder)
            result = check_integrity(root, db)
            st.session_state.last_result = result
            logging.info("Manual integrity check completed for %s", root)
        except (OSError, ValueError) as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Real-time monitoring")
    if st.button("Start real-time watcher", use_container_width=True):
        try:
            root = validate_directory(folder)
            old = st.session_state.observer
            if old is not None:
                old.stop()
                old.join(timeout=2)

            def record_live_event(event_type: str, absolute_path: str) -> None:
                try:
                    relative = Path(absolute_path).resolve().relative_to(root).as_posix()
                except (ValueError, OSError):
                    relative = absolute_path
                db.add_event(f"LIVE_{event_type}", relative)
                logging.info("Live event %s: %s", event_type, relative)

            st.session_state.observer = start_monitor(root, record_live_event)
            st.success("Real-time watcher started.")
        except (OSError, ValueError, RuntimeError) as exc:
            st.error(str(exc))

    if st.button("Stop real-time watcher", use_container_width=True):
        observer = st.session_state.observer
        if observer is not None:
            observer.stop()
            observer.join(timeout=3)
            st.session_state.observer = None
            st.success("Real-time watcher stopped.")
        else:
            st.info("Real-time watcher is not running.")

    st.divider()
    st.subheader("Periodic integrity checks")
    interval = st.number_input("Interval (seconds)", min_value=5, max_value=3600, value=60, step=5)
    if st.button("Start periodic checks", use_container_width=True):
        try:
            root = validate_directory(folder)
            monitor = st.session_state.periodic_monitor
            if monitor is not None:
                monitor.stop()
            monitor = PeriodicMonitor(root, db, int(interval))
            monitor.start()
            st.session_state.periodic_monitor = monitor
            st.success("Periodic checks started.")
        except (OSError, ValueError) as exc:
            st.error(str(exc))

    if st.button("Stop periodic checks", use_container_width=True):
        monitor = st.session_state.periodic_monitor
        if monitor is not None:
            monitor.stop()
            st.session_state.periodic_monitor = None
            st.success("Periodic checks stopped.")
        else:
            st.info("Periodic checks are not running.")

baseline = db.get_baseline()
events = db.get_events(limit=500)
event_counts = {
    name: sum(event["event_type"] == name for event in events)
    for name in ("ADDED", "MODIFIED", "DELETED")
}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Baseline files", len(baseline))
c2.metric("Added detections", event_counts["ADDED"])
c3.metric("Modified detections", event_counts["MODIFIED"])
c4.metric("Deleted detections", event_counts["DELETED"])

st.divider()
st.subheader("Latest integrity check")
result = st.session_state.last_result
if result is None:
    st.info("Create a baseline, then run an integrity check to see changes.")
else:
    a, m, d = st.columns(3)
    a.metric("Added", len(result["added"]))
    m.metric("Modified", len(result["modified"]))
    d.metric("Deleted", len(result["deleted"]))
    for key, label in (
        ("added", "Added files"),
        ("modified", "Modified files"),
        ("deleted", "Deleted files"),
    ):
        with st.expander(f"{label} ({len(result[key])})", expanded=bool(result[key])):
            if result[key]:
                st.dataframe(result[key], use_container_width=True, hide_index=True)
            else:
                st.write("No changes detected.")

st.divider()
st.subheader("Event history")
if events:
    st.dataframe(events, use_container_width=True, hide_index=True)
else:
    st.write("No events recorded yet.")

with st.expander("Security notes"):
    st.markdown("""
    - SHA-256 detects content changes; file timestamps are metadata, not the integrity decision.
    - Keep the SQLite database and backups outside the monitored directory.
    - A local baseline is not tamper-proof if an attacker can modify both monitored files and the database.
    - Real-time events are notifications. Periodic/manual hash comparisons verify file contents against the baseline.
    - This is an educational prototype, not a tamper-proof enterprise security product.
    """)
