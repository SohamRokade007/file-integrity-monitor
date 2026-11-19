"""Application logging configuration."""
import logging
from pathlib import Path


def configure_logging() -> None:
    Path("data").mkdir(exist_ok=True)
    logging.basicConfig(
        filename="data/fim.log",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
