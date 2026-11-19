"""Streaming SHA-256 utilities."""
from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_sha256(file_path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a SHA-256 digest, reading large files in bounded chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
