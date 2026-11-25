"""
Portable Configuration, State, CDP Reachability & Cross-Platform File Lock Loader.

Resolution order for base directory:
  1. ``$YT_PRO_HOME`` environment variable (if set)
  2. Current working directory (if ``config.json`` exists there)
  3. Parent of this script's directory (skill repo root)

All scripts import :func:`load_config` to get channel settings without
hardcoding any paths or channel IDs.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.request
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import CDP_DEFAULT_URL, CDP_HTTP_TIMEOUT_S, CDP_VERSION_ENDPOINT

__all__ = [
    "BASE_DIR",
    "load_config",
    "validate_config",
    "is_cdp_available",
    "load_json",
    "save_json",
    "acquire_process_lock",
]


# ── Base directory resolution ───────────────────────────────────────────

def get_base_dir() -> Path:
    """Resolve the project root directory.

    Checks (in order): ``$YT_PRO_HOME`` env var, ``./config.json`` in
    cwd, then falls back to the parent of this script's directory.
    """
    env_home = os.environ.get("YT_PRO_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()
    cwd_cfg = Path.cwd() / "config.json"
    if cwd_cfg.exists():
        return Path.cwd().resolve()
    return Path(__file__).resolve().parent.parent


BASE_DIR: Path = get_base_dir()
CONFIG_FILE: Path = BASE_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "channel_id": None,
    "channel_name": "Your Gaming Channel",
    "channel_handle": "",
    "cdp_url": CDP_DEFAULT_URL,
    "target_audience": "USA / Tier-1 English",
    "video_language": "English (United States)",
    "default_category": "Gaming",
    "default_game_title": "Grand Theft Auto VI",
    "playlists": [
        "GTA 6 4K Gameplay & Physics",
        "GTA 6 Viral Clips & Streamer Reactions",
    ],
    "morning_window_hours": [18, 21],
    "night_window_start_hour": 21,
    "ig_profile_url": "https://www.instagram.com/",
    "catalog_path": str(BASE_DIR / "queue" / "catalog.json"),
    "history_path": str(BASE_DIR / "youtube_shorts_history.json"),
    "channel_state_path": str(BASE_DIR / "youtube_channel_state.json"),
    "audit_path": str(BASE_DIR / "youtube_channel_audit.json"),
    "analytics_history_path": str(BASE_DIR / "youtube_analytics_history.json"),
    "comments_log_path": str(BASE_DIR / "youtube_comments_log.json"),
    "watermark_path": str(BASE_DIR / "assets" / "watermark_150.png"),
}


# ── Config I/O & Validation ────────────────────────────────────────────

def load_config() -> dict[str, Any]:
    """Load and merge user config over defaults.

    ``None`` values in the user file are skipped so defaults are preserved.
    """
    cfg: dict[str, Any] = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            user_cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in user_cfg.items() if v is not None})
        except (json.JSONDecodeError, OSError) as exc:
            import logging
            logging.getLogger("yt_pro.config").warning(
                "Could not parse %s: %s", CONFIG_FILE, exc,
            )
    return cfg


def validate_config(cfg: dict[str, Any] | None = None, require_channel_id: bool = True) -> dict[str, Any]:
    """Validate configuration fields and types, raising on invalid values.

    Args:
        cfg: Pre-loaded config dict. If ``None``, calls :func:`load_config`.
        require_channel_id: When ``True``, requires ``channel_id`` to be non-empty.

    Returns:
        The validated config dict.

    Raises:
        ConfigMissingFieldError: If ``channel_id`` is missing when required.
        ConfigError: If ``cdp_url`` or schedule hour fields have invalid types/ranges.
    """
    from exceptions import ConfigError, ConfigMissingFieldError

    if cfg is None:
        cfg = load_config()

    if require_channel_id and not cfg.get("channel_id"):
        raise ConfigMissingFieldError("channel_id")

    cdp_url = str(cfg.get("cdp_url", ""))
    if not cdp_url.startswith(("http://", "https://")):
        raise ConfigError(f"Invalid cdp_url '{cdp_url}': must start with http:// or https://")

    win = cfg.get("morning_window_hours")
    if not isinstance(win, (list, tuple)) or len(win) != 2 or not all(isinstance(h, int) and 0 <= h <= 23 for h in win):
        raise ConfigError(f"Invalid morning_window_hours '{win}': expected [start_hour, end_hour] in 0..23")

    night_h = cfg.get("night_window_start_hour")
    if not isinstance(night_h, int) or not (0 <= night_h <= 23):
        raise ConfigError(f"Invalid night_window_start_hour '{night_h}': expected integer in 0..23")

    return cfg


# ── CDP Reachability ───────────────────────────────────────────────────

def is_cdp_available(host: str | None = None, timeout: float = CDP_HTTP_TIMEOUT_S) -> bool:
    """Return ``True`` if the Chrome DevTools Protocol HTTP endpoint responds."""
    cdp = (host or load_config()["cdp_url"]).rstrip("/")
    try:
        req = urllib.request.Request(f"{cdp}{CDP_VERSION_ENDPOINT}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


# ── JSON helpers ────────────────────────────────────────────────────────

def load_json(path: str | Path, default: Any = None) -> Any:
    """Load a JSON file, returning *default* if missing or corrupt."""
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return default if default is not None else {}


def save_json(path: str | Path, data: Any) -> None:
    """Write *data* as pretty-printed JSON, creating parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Cross-platform process lock ────────────────────────────────────────

@contextmanager
def acquire_process_lock(lock_name: str = "yt_pro_pipeline.lock") -> Generator[bool, None, None]:
    """Single-instance lock supporting both Windows (msvcrt) and POSIX (fcntl).

    Yields ``True`` if the lock was acquired, ``False`` if another instance
    already holds it.
    """
    lock_path = BASE_DIR / lock_name
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_path, "a+", encoding="utf-8")
    locked = False
    try:
        if os.name == "nt":
            import msvcrt
            fp.seek(0)
            msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        fp.truncate(0)
        fp.write(f"pid={os.getpid()} started={datetime.datetime.now().isoformat()}\n")
        fp.flush()
        yield True
    except OSError:
        yield False
    finally:
        if locked:
            try:
                if os.name == "nt":
                    import msvcrt
                    fp.seek(0)
                    msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
        fp.close()
