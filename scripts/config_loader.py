"""
Portable Configuration, State & Cross-Platform File Lock Loader
for youtube-shorts-pro-skill.

Resolution order for base directory:
  1. $YT_PRO_HOME environment variable (if set)
  2. Current working directory (if config.json exists there)
  3. Parent of this script's directory (skill repo root)

All scripts import load_config() to get channel settings without
hardcoding any paths or channel IDs.
"""

import json
import os
from contextlib import contextmanager
from pathlib import Path
import datetime


def get_base_dir() -> Path:
    env_home = os.environ.get("YT_PRO_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()
    cwd_cfg = Path.cwd() / "config.json"
    if cwd_cfg.exists():
        return Path.cwd().resolve()
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "channel_id": None,
    "channel_name": "Your Gaming Channel",
    "channel_handle": "",
    "cdp_url": "http://localhost:9222",
    "target_audience": "USA / Tier-1 English",
    "video_language": "English (United States)",
    "default_category": "Gaming",
    "default_game_title": "Grand Theft Auto VI",
    "playlists": [
        "GTA 6 4K Gameplay & Physics",
        "GTA 6 Viral Clips & Streamer Reactions",
    ],
    "morning_window_hours": [18, 21],  # Default EST morning converted to host local time
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


def load_config() -> dict:
    """Load and merge user config over defaults. None values in user file are skipped."""
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            user_cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in user_cfg.items() if v is not None})
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[CONFIG] Warning: could not parse {CONFIG_FILE}: {exc}")
    return cfg


def load_json(path: str | Path, default=None):
    """Load a JSON file, returning *default* (or None) if missing or corrupt."""
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return default if default is not None else {}


def save_json(path: str | Path, data) -> None:
    """Atomically write *data* as pretty-printed JSON to *path*."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


@contextmanager
def acquire_process_lock(lock_name: str = "yt_pro_pipeline.lock"):
    """Single-instance lock supporting both Windows (msvcrt) and POSIX (fcntl)."""
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
