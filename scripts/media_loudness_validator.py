"""
Media, Audio Loudness & Pro Metadata Readiness Validator.

Validates queued Shorts against:
  - 9:16 vertical aspect ratio (1080×1920)
  - Duration ≤ 60 s
  - AAC/audio stream presence
  - Broadcast loudness (-38 dBFS to -3 dBFS via FFmpeg volumedetect)
  - Title ≤ 60 chars with ``#Shorts`` hashtag
  - Required metadata fields (game_title, playlist_name, pinned_comment)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (
    FFMPEG_VOLUMEDETECT_TIMEOUT_S,
    FFPROBE_CHECK_TIMEOUT_S,
    LOUDNESS_MAX_DB,
    LOUDNESS_MIN_DB,
    MAX_TITLE_LENGTH,
    REQUIRED_HASHTAG,
    SHORTS_ASPECT_HEIGHT,
    SHORTS_ASPECT_TOLERANCE,
    SHORTS_ASPECT_WIDTH,
    SHORTS_MAX_DURATION_S,
)
from exceptions import FFmpegNotFoundError
from logger import get_logger

log = get_logger(__name__)

__all__ = ["probe_video", "check_audio_loudness", "verify_catalog_items"]


def _check_ffmpeg_available() -> bool:
    """Return ``True`` if both ``ffprobe`` and ``ffmpeg`` are reachable in PATH."""
    try:
        for tool in ("ffprobe", "ffmpeg"):
            subprocess.run([tool, "-version"], capture_output=True, timeout=FFPROBE_CHECK_TIMEOUT_S)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def probe_video(video_path: str) -> dict[str, Any]:
    """Inspect a video file with ffprobe for resolution, duration, and audio stream.

    Args:
        video_path: Absolute path to the video file.

    Returns:
        Dict with keys: width, height, duration, size_bytes, size_mb,
        has_audio, video_codec, is_9_16, under_60s, error.
    """
    if not os.path.exists(video_path):
        return {"error": f"File not found: {video_path}"}

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,r_frame_rate,codec_name",
        "-show_entries", "format=duration,size,bit_rate",
        "-of", "json", video_path,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        vstream = data.get("streams", [{}])[0] if data.get("streams") else {}
        fmt = data.get("format", {})

        w = int(vstream.get("width", 0))
        h = int(vstream.get("height", 0))
        dur = float(vstream.get("duration") or fmt.get("duration", 0))
        size_bytes = int(fmt.get("size", 0)) or os.path.getsize(video_path)

        audio_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,channels,sample_rate",
            "-of", "json", video_path,
        ]
        ares = subprocess.run(audio_cmd, capture_output=True, text=True)
        adata = json.loads(ares.stdout) if ares.stdout else {}
        has_audio = len(adata.get("streams", [])) > 0

        is_9_16 = (
            (w == SHORTS_ASPECT_WIDTH and h == SHORTS_ASPECT_HEIGHT)
            or (h > 0 and abs((w / h) - (9 / 16)) < SHORTS_ASPECT_TOLERANCE)
        )

        return {
            "width": w,
            "height": h,
            "duration": round(dur, 2),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "has_audio": has_audio,
            "video_codec": vstream.get("codec_name", "unknown"),
            "is_9_16": is_9_16,
            "under_60s": dur <= SHORTS_MAX_DURATION_S,
            "error": None,
        }
    except FileNotFoundError:
        return {"error": "ffprobe not found in PATH. Install FFmpeg: https://ffmpeg.org/"}
    except Exception as exc:
        return {"error": f"FFprobe failed: {exc}"}


def check_audio_loudness(video_path: str) -> dict[str, Any]:
    """Measure mean & max volume via FFmpeg volumedetect.

    Guards against near-silent (< -38 dBFS) and clipping (> -3 dBFS) audio.

    Args:
        video_path: Absolute path to the video file.

    Returns:
        Dict with keys: ok, mean_db, max_db, error.
    """
    if not os.path.exists(video_path):
        return {"ok": False, "mean_db": None, "max_db": None, "error": "file missing"}

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    cmd = ["ffmpeg", "-hide_banner", "-i", video_path, "-af", "volumedetect", "-f", "null", null_sink]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=FFMPEG_VOLUMEDETECT_TIMEOUT_S)
        mean_db = max_db = None

        for line in (res.stderr or "").splitlines():
            if "mean_volume:" in line:
                try:
                    mean_db = float(line.split("mean_volume:")[-1].replace("dB", "").strip())
                except ValueError:
                    pass
            elif "max_volume:" in line:
                try:
                    max_db = float(line.split("max_volume:")[-1].replace("dB", "").strip())
                except ValueError:
                    pass

        ok = mean_db is not None and LOUDNESS_MIN_DB <= mean_db <= LOUDNESS_MAX_DB
        return {"ok": ok, "mean_db": mean_db, "max_db": max_db, "error": None}
    except FileNotFoundError:
        return {"ok": False, "mean_db": None, "max_db": None, "error": "ffmpeg not found in PATH"}
    except subprocess.TimeoutExpired:
        msg = f"ffmpeg timed out after {FFMPEG_VOLUMEDETECT_TIMEOUT_S}s"
        return {"ok": False, "mean_db": None, "max_db": None, "error": msg}
    except Exception as exc:
        return {"ok": False, "mean_db": None, "max_db": None, "error": str(exc)}


def verify_catalog_items(
    catalog: list[dict],
    check_loudness: bool = True,
    raise_on_missing_ffmpeg: bool = False,
) -> bool:
    """Validate every queued Short against resolution, duration, loudness, and metadata rules.

    Args:
        catalog: List of catalog entry dicts.
        check_loudness: Whether to run FFmpeg volumedetect (slower but thorough).
        raise_on_missing_ffmpeg: Raise :class:`FFmpegNotFoundError` instead of returning ``False``.

    Returns:
        ``True`` if all entries pass, ``False`` if any fail.

    Raises:
        FFmpegNotFoundError: If ``raise_on_missing_ffmpeg=True`` and FFmpeg is absent.
    """
    if not catalog:
        log.error("Catalog is empty — nothing to validate.")
        return False

    if not _check_ffmpeg_available():
        if raise_on_missing_ffmpeg:
            raise FFmpegNotFoundError()
        log.error("ffmpeg/ffprobe not found in PATH. Install FFmpeg: https://ffmpeg.org/")
        return False

    total = len(catalog)
    passed = 0
    log.info("═" * 72)
    log.info("  AUDITING %d YOUTUBE SHORTS (MEDIA + LOUDNESS + METADATA)", total)
    log.info("═" * 72)

    for idx, entry in enumerate(catalog, 1):
        eid = entry.get("id", f"item_{idx}")
        vpath = entry.get("video_path", "")
        yt = entry.get("youtube_shorts", {})
        title = yt.get("title", "")

        pr = probe_video(vpath)
        if pr.get("error"):
            log.error("  [%02d] FAIL │ %-36s │ %s", idx, eid, pr["error"])
            continue

        loud_ok = True
        mean_str = "  n/a"
        if check_loudness and pr.get("has_audio"):
            ld = check_audio_loudness(vpath)
            loud_ok = ld.get("ok", False)
            if ld.get("mean_db") is not None:
                mean_str = f"{ld['mean_db']:>5.1f}dB"

        title_ok = len(title) <= MAX_TITLE_LENGTH and REQUIRED_HASHTAG in title
        meta_ok = bool(yt.get("game_title") and yt.get("playlist_name") and yt.get("pinned_comment"))
        ok = pr["is_9_16"] and pr["under_60s"] and pr["has_audio"] and loud_ok and title_ok and meta_ok

        if ok:
            passed += 1

        status = "PASS" if ok else "FAIL"
        meta_label = "OK" if meta_ok else "MISS"
        log.info(
            "  [%02d] %s │ %-36s │ %dx%d │ %5.1fs │ %s │ meta=%s │ title=%dc",
            idx, status, eid, pr["width"], pr["height"],
            pr["duration"], mean_str, meta_label, len(title),
        )

    log.info("─" * 72)
    log.info("  RESULT: %d/%d PASSED", passed, total)
    log.info("═" * 72)
    return passed == total


def main() -> None:
    """Standalone CLI for validating a single video or catalog JSON."""
    parser = argparse.ArgumentParser(description="Validate YouTube Shorts media & metadata")
    parser.add_argument("--catalog", help="Path to catalog.json file")
    parser.add_argument("--file", help="Path to a single .mp4 file to probe")
    parser.add_argument("--no-loudness", action="store_true", help="Skip FFmpeg volumedetect")
    args = parser.parse_args()

    if args.file:
        if not _check_ffmpeg_available():
            raise FFmpegNotFoundError()
        pr = probe_video(args.file)
        ld = check_audio_loudness(args.file) if not args.no_loudness and not pr.get("error") else {}
        log.info("Probe: %s", json.dumps(pr))
        if ld:
            log.info("Loudness: %s", json.dumps(ld))
        ok = not pr.get("error") and pr.get("is_9_16") and pr.get("under_60s") and ld.get("ok", True)
        sys.exit(0 if ok else 1)

    if args.catalog:
        data = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
        ok = verify_catalog_items(data, check_loudness=not args.no_loudness, raise_on_missing_ffmpeg=True)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
