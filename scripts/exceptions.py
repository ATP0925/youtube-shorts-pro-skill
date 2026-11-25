"""
Custom exception hierarchy for youtube-shorts-pro-skill.

All exceptions inherit from YTProError so callers can catch broadly
or narrowly as needed.
"""

from __future__ import annotations

__all__ = [
    "YTProError",
    "ConfigError",
    "ConfigMissingFieldError",
    "CDPConnectionError",
    "AuthGateError",
    "MediaValidationError",
    "FFmpegNotFoundError",
    "UploadError",
    "DuplicateUploadError",
    "IGSafetyError",
    "PipelineLockError",
    "CatalogEmptyError",
]


class YTProError(Exception):
    """Base exception for all youtube-shorts-pro-skill errors."""


# ── Configuration ───────────────────────────────────────────────────────
class ConfigError(YTProError):
    """Raised when config.json is missing, invalid, or lacks required fields."""


class ConfigMissingFieldError(ConfigError):
    """Raised when a specific required config field is absent or null."""

    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(f"Required config field '{field}' is missing or null.")


# ── CDP / Browser ───────────────────────────────────────────────────────
class CDPConnectionError(YTProError):
    """Raised when Chrome DevTools Protocol endpoint is unreachable."""

    def __init__(self, cdp_url: str, detail: str = "") -> None:
        self.cdp_url = cdp_url
        msg = f"Cannot connect to CDP at {cdp_url}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class AuthGateError(YTProError):
    """Raised when Google auth/2FA/checkpoint blocks automation.

    The pipeline MUST stop cleanly — never attempt to bypass.
    """

    def __init__(self, url: str = "", trigger: str = "") -> None:
        self.url = url
        self.trigger = trigger
        msg = "Google authentication gate detected"
        if trigger:
            msg += f" ('{trigger}')"
        if url:
            msg += f" at {url}"
        msg += ". Manual verification required in Chrome."
        super().__init__(msg)


# ── Media Validation ───────────────────────────────────────────────────
class MediaValidationError(YTProError):
    """Raised when a video file fails pre-upload quality checks."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Media validation failed for '{path}': {reason}")


class FFmpegNotFoundError(MediaValidationError):
    """Raised when ffmpeg/ffprobe is not found in PATH."""

    def __init__(self) -> None:
        super().__init__("ffmpeg", "ffmpeg/ffprobe not found in PATH. Install from https://ffmpeg.org/")


# ── Upload ──────────────────────────────────────────────────────────────
class UploadError(YTProError):
    """Raised when a YouTube Studio upload fails or times out."""

    def __init__(self, video_path: str, detail: str = "") -> None:
        self.video_path = video_path
        msg = f"Upload failed for '{video_path}'"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class DuplicateUploadError(UploadError):
    """Raised when the same slot has already been uploaded today."""

    def __init__(self, slot: str, date: str) -> None:
        self.slot = slot
        self.date = date
        super().__init__("", f"Slot '{slot}' already uploaded on {date}")


# ── Instagram ──────────────────────────────────────────────────────────
class IGSafetyError(YTProError):
    """Raised when Instagram safety circuit breaker triggers.

    Covers: account suspended, action blocked, checkpoint, login required.
    The pipeline MUST halt — never bypass checkpoints.
    """

    def __init__(self, indicator: str, url: str = "") -> None:
        self.indicator = indicator
        self.url = url
        msg = f"Instagram safety trigger: '{indicator}'"
        if url:
            msg += f" at {url}"
        msg += ". Automation halted."
        super().__init__(msg)


# ── Pipeline ────────────────────────────────────────────────────────────
class PipelineLockError(YTProError):
    """Raised when another pipeline instance holds the process lock."""

    def __init__(self) -> None:
        super().__init__("Another pipeline instance is already running. Remove the lock file or wait.")


class CatalogEmptyError(YTProError):
    """Raised when no eligible Shorts remain in the upload catalog."""

    def __init__(self) -> None:
        super().__init__("All queued Shorts have been uploaded or no eligible entries remain.")
