"""
Centralized logging for youtube-shorts-pro-skill.

Usage in any module:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Upload complete for %s", video_id)

Features:
  - Console handler with level-prefixed formatting
  - Rotating file handler (5 MB × 3 backups) in logs/yt_pro.log
  - Single setup call ensures handlers are attached only once
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (
    LOG_BACKUP_COUNT,
    LOG_DATE_FORMAT,
    LOG_DIR_NAME,
    LOG_FILE_NAME,
    LOG_FORMAT,
    LOG_MAX_BYTES,
)

__all__ = ["get_logger"]

_INITIALIZED = False


def _setup_root_logger() -> None:
    """Configure root logger with console + rotating file handlers (called once)."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    root = logging.getLogger("yt_pro")
    root.setLevel(logging.DEBUG)

    # ── Console handler ─────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    root.addHandler(console)

    # ── File handler (rotating) ─────────────────────────────────────
    try:
        try:
            from config_loader import BASE_DIR
            log_dir = BASE_DIR / LOG_DIR_NAME
        except ImportError:
            log_dir = Path.cwd() / LOG_DIR_NAME

        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_dir / LOG_FILE_NAME),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        root.addHandler(file_handler)
    except (OSError, PermissionError):
        root.warning("Could not create log file handler; logging to console only.")


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'yt_pro' namespace.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    _setup_root_logger()
    short = name.replace("scripts.", "").replace("__main__", "pipeline")
    return logging.getLogger(f"yt_pro.{short}")
