# File Integrity Monitoring System (FIMS)

A Python-based File Integrity Monitoring System that uses **SHA-256** checksums to detect file additions, modifications and deletions. It includes a Streamlit dashboard, SQLite event history, real-time notifications and periodic integrity checks.

## Features

- Streaming SHA-256 hashing for files of different sizes.
- Create or replace a baseline for a selected directory.
- Detect added, modified and deleted files by comparing content hashes.
- Store the baseline and event history in SQLite.
- Real-time filesystem notifications using Watchdog.
- Periodic integrity checks using a background thread.
- Streamlit dashboard for scan results and event history.
- Unit tests for hashing and integrity comparison.

## Project structure

```text
file-integrity-monitor/
├── app.py
├── core/
│   ├── hasher.py
│   ├── integrity.py
│   ├── monitor.py
│   ├── scanner.py
│   └── scheduler.py
├── database/
│   └── db_manager.py
├── monitored_files/
├── tests/
│   ├── test_hasher.py
│   └── test_integrity.py
├── data/
├── requirements.txt
└── README.md
```

## Run locally

Python 3.10 or newer is recommended.

1. Clone the repository:

   ```bash
   git clone https://github.com/SohamRokade007/file-integrity-monitor.git
   cd file-integrity-monitor
   ```

2. Create and activate a virtual environment.

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

5. In the sidebar, use `monitored_files` as the directory. Create a baseline first, then add, modify or delete a test file and run an integrity check.

## Run tests

```bash
python -m pytest -q
```

## How it works

1. The scanner walks the selected directory and computes a SHA-256 digest for every regular file.
2. Creating a baseline stores each relative path, digest, file size and modification time in SQLite.
3. An integrity check scans the directory again and compares its content hashes with the baseline.
4. A path absent from the baseline is reported as **ADDED**.
5. A matching path with a different SHA-256 digest is reported as **MODIFIED**.
6. A baseline path missing from the current scan is reported as **DELETED**.

The baseline records the directory it belongs to, preventing accidental comparison against a different folder. File size and modification time are stored as metadata; the SHA-256 digest determines content changes.

## Monitoring modes

- **Manual:** Run an integrity check from the dashboard whenever required.
- **Real-time:** Watchdog records filesystem activity as it occurs. These notifications are useful alerts; run a hash comparison to verify the content against the baseline.
- **Periodic:** A background thread runs integrity comparisons at the configured interval while the dashboard process remains active.

## Security considerations

- Start with the included test folder. Do not select your Windows directory, entire user profile or whole system drive.
- Keep `data/fim.db` and its backups outside the monitored folder. The dashboard blocks selecting a directory that contains its own database.
- Protect the baseline database. An attacker who can modify both monitored files and the database could tamper with reference hashes.
- Do not treat real-time filesystem notifications alone as proof of content integrity.
- This is an educational prototype, not a tamper-proof enterprise security product.

## Current scope and future improvements

Implemented: local scanning, SHA-256 hashing, baseline comparison, SQLite history, manual checks, Watchdog notifications, periodic checks, Streamlit dashboard and tests.

Possible future work: signed or remote baselines, configurable exclusions, downloadable reports, alert notifications and role-based access.

## License

MIT. See [LICENSE](LICENSE).
