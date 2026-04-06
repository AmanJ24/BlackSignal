"""
Centralized logging configuration for the BlackSignal pipeline.
Import this module early (e.g., in settings.py or run_pipeline.py) to
configure logging once for the entire application.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_dir: str | Path = None, level: int = logging.INFO):
    """
    Configure logging for the entire pipeline.
    
    - Console: colored, human-readable output
    - File: structured, rotated log files
    """
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Clear any existing handlers (prevents duplicate logs)
    root.handlers.clear()

    # --- Console Handler ---
    console = logging.StreamHandler()
    console.setLevel(level)
    console_fmt = logging.Formatter(
        "%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
        datefmt="%H:%M:%S"
    )
    console.setFormatter(console_fmt)
    root.addHandler(console)

    # --- File Handler (Rotating, 5MB max, 3 backups) ---
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "pipeline.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Capture everything to file
    file_fmt = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s"
    )
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    # Reduce noise from third-party libs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("stem").setLevel(logging.WARNING)

    logging.getLogger("BlackSignal").info("✅ Logging initialized.")
