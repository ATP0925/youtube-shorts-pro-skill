"""
Viral Hook, Pacing & Retention Readiness Analyzer.

Evaluates short-form vertical videos using FFmpeg/FFprobe telemetry against
the viral engineering heuristics defined in ``references/viral-hooks-retention.md``:
  - Opening 0–3s hook audio energy vs. overall average
  - Opening 0–1.5s black/blank-frame swipe-away hazard detection
  - Visual pacing & cuts-per-minute (scene-change density via FFmpeg)
  - Vertical 9:16 format + optimal viral duration sweet spot (15–35s)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (
    BLACKFRAME_MIN_DURATION_S,
    BLACKFRAME_PIX_THRESHOLD,
    FFMPEG_VOLUMEDETECT_TIMEOUT_S,
    HOOK_MIN_LOUDNESS_DB,
    HOOK_WINDOW_S,
    MIN_CUTS_PER_MINUTE,
    SCENE_DETECT_THRESHOLD,
    VIRAL_SWEET_SPOT_MAX_S,
    VIRAL_SWEET_SPOT_MIN_S,
)
from exceptions import FFmpegNotFoundError
from logger import get_logger
from media_loudness_validator import _check_ffmpeg_available, check_audio_loudness, probe_video

log = get_logger(__name__)

__all__ = ["analyze_hook_audio", "detect_opening_blackframes", "measure_visual_pacing", "analyze_viral_readiness"]


def _parse_volumedetect(stderr: str) -> tuple[float | None, float | None]:
    """Extract mean_volume and max_volume (dBFS) from FFmpeg volumedetect stderr."""
    mean_db = max_db = None
    for line in (stderr or "").splitlines():
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
    return mean_db, max_db


def analyze_hook_audio(video_path: str, window_s: float = HOOK_WINDOW_S) -> dict[str, Any]:
    """Measure mean and peak loudness during the opening hook window (0–3s)."""
    if not os.path.exists(video_path):
        return {"ok": False, "mean_db": None, "max_db": None, "error": "file missing"}

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    cmd = [
        "ffmpeg", "-hide_banner", "-t", str(window_s), "-i", video_path,
        "-af", "volumedetect", "-f", "null", null_sink,
    ]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=FFMPEG_VOLUMEDETECT_TIMEOUT_S,
        )
        mean_db, max_db = _parse_volumedetect(res.stderr)
        ok = mean_db is not None and mean_db >= HOOK_MIN_LOUDNESS_DB
        return {"ok": ok, "mean_db": mean_db, "max_db": max_db, "error": None}
    except FileNotFoundError:
        return {"ok": False, "mean_db": None, "max_db": None, "error": "ffmpeg not found"}
    except Exception as exc:
        return {"ok": False, "mean_db": None, "max_db": None, "error": str(exc)}


def detect_opening_blackframes(video_path: str, window_s: float = 2.0) -> dict[str, Any]:
    """Check if the opening frames contain black/blank frames that trigger instant swipes."""
    if not os.path.exists(video_path):
        return {"has_opening_black": False, "events": [], "error": "file missing"}

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    vf = f"blackdetect=d={BLACKFRAME_MIN_DURATION_S}:pix_th={BLACKFRAME_PIX_THRESHOLD}"
    cmd = ["ffmpeg", "-hide_banner", "-t", str(window_s), "-i", video_path, "-vf", vf, "-f", "null", null_sink]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=FFMPEG_VOLUMEDETECT_TIMEOUT_S,
        )
        events: list[dict[str, float]] = []
        for line in (res.stderr or "").splitlines():
            if "black_start:" in line:
                ms = re.search(r"black_start:([\d.]+)\s+black_end:([\d.]+)\s+black_duration:([\d.]+)", line)
                if ms:
                    s, e, d = float(ms.group(1)), float(ms.group(2)), float(ms.group(3))
                    if s < 1.5:
                        events.append({"start": s, "end": e, "duration": d})
        return {"has_opening_black": len(events) > 0, "events": events, "error": None}
    except Exception as exc:
        return {"has_opening_black": False, "events": [], "error": str(exc)}


def measure_visual_pacing(video_path: str, duration_s: float) -> dict[str, Any]:
    """Count visual scene transitions / cuts using FFmpeg ``scenedetect``."""
    if not os.path.exists(video_path) or duration_s <= 0:
        return {"cuts": 0, "cuts_per_minute": 0.0, "avg_shot_s": duration_s}

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    vf = f"select='gt(scene,{SCENE_DETECT_THRESHOLD})',showinfo"
    cmd = [
        "ffmpeg", "-hide_banner", "-i", video_path, "-an",
        "-vf", vf, "-f", "null", null_sink,
    ]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=FFMPEG_VOLUMEDETECT_TIMEOUT_S,
        )
        timestamps = [
            float(m.group(1))
            for m in re.finditer(r"pts_time:([\d.]+)", res.stderr or "")
        ]
        cuts = len(timestamps)
        cpm = round((cuts / duration_s) * 60.0, 1)
        avg_shot = round(duration_s / max(1, cuts + 1), 2)
        return {
            "cuts": cuts,
            "cuts_per_minute": cpm,
            "avg_shot_s": avg_shot,
            "cut_timestamps": [round(t, 2) for t in timestamps[:20]],
        }
    except Exception as exc:
        return {"cuts": 0, "cuts_per_minute": 0.0, "avg_shot_s": duration_s, "error": str(exc)}


def analyze_viral_readiness(video_path: str) -> dict[str, Any]:
    """Run all viral readiness checks on a video and compute a 0–100 score.

    Scoring breakdown (100 points total):
      - Format & Audio (25 pts): 9:16 vertical, audio stream present, broadcast loudness
      - Opening Hook 0–3s (35 pts): strong hook audio energy, zero opening black frames
      - Visual Pacing (25 pts): cuts/min >= MIN_CUTS_PER_MINUTE or dynamic motion density
      - Duration Sweet Spot (15 pts): 15–35s optimal range (<= 60s partial)
    """
    probe = probe_video(video_path)
    if probe.get("error"):
        return {"video_path": video_path, "score": 0, "grade": "F", "error": probe["error"], "recommendations": []}

    dur = float(probe.get("duration") or 0.0)
    full_loud = check_audio_loudness(video_path) if probe.get("has_audio") else {"ok": False, "mean_db": None}
    hook_loud = analyze_hook_audio(video_path) if probe.get("has_audio") else {"ok": False, "mean_db": None}
    black = detect_opening_blackframes(video_path)
    pacing = measure_visual_pacing(video_path, dur)

    score = 0
    recs: list[str] = []

    # 1. Format & Overall Loudness (25 pts)
    if probe.get("is_9_16"):
        score += 10
    else:
        recs.append("Reframe to 1080x1920 (9:16) with blurred background or dynamic crop.")

    if probe.get("has_audio") and full_loud.get("ok"):
        score += 15
    else:
        recs.append("Normalize audio to -14 LUFS using loudnorm=I=-14:LRA=7:tp=-1.5.")

    # 2. Opening 0–3s Hook Execution (35 pts)
    if not black.get("has_opening_black"):
        score += 15
    else:
        recs.append("Trim opening black/blank frames cleanly so motion starts on frame 1.")

    h_db = hook_loud.get("mean_db")
    f_db = full_loud.get("mean_db")
    if hook_loud.get("ok") and h_db is not None:
        score += 15
        if f_db is not None and h_db >= (f_db - 2.0):
            score += 5
        else:
            recs.append("First 3s audio is softer than video average — add impact/whoosh SFX at 0.0s.")
    else:
        recs.append("Opening 0–3s audio is weak/silent (< -30 dB) — eliminate dead air at start.")

    # 3. Visual Pacing (25 pts)
    cpm = pacing.get("cuts_per_minute", 0.0)
    if cpm >= MIN_CUTS_PER_MINUTE:
        score += 25
    elif cpm >= 4.0:
        score += 15
        recs.append(f"Moderate pacing ({cpm} cuts/min) — inject zoom-ins, B-roll, or speed ramps every 3–4s.")
    else:
        score += 5
        recs.append(f"Low scene-cut pacing ({cpm} cuts/min) — add speed ramps or visual interrupts every 2.5–4s.")

    # 4. Duration Sweet Spot (15 pts)
    if VIRAL_SWEET_SPOT_MIN_S <= dur <= VIRAL_SWEET_SPOT_MAX_S:
        score += 15
    elif probe.get("under_60s"):
        score += 8
        if dur < VIRAL_SWEET_SPOT_MIN_S:
            recs.append(f"Clip is short ({dur:.1f}s) — aim for 15–35s or design a seamless loop ending.")
        else:
            recs.append(f"Clip is {dur:.1f}s — tightening to 20–35s protects >90% completion rate.")
    else:
        recs.append("Exceeds 60s YouTube Shorts cutoff — trim below 60s.")

    grade = "S" if score >= 90 else ("A" if score >= 80 else ("B" if score >= 65 else ("C" if score >= 50 else "D")))
    return {
        "video_path": video_path,
        "file_name": os.path.basename(video_path),
        "score": score,
        "grade": grade,
        "resolution": f"{probe['width']}x{probe['height']}",
        "duration_s": dur,
        "overall_mean_db": f_db,
        "hook_3s_mean_db": h_db,
        "opening_blackframe": black.get("has_opening_black", False),
        "cuts": pacing.get("cuts", 0),
        "cuts_per_minute": cpm,
        "avg_shot_s": pacing.get("avg_shot_s", dur),
        "recommendations": recs,
    }


def main() -> None:
    """Standalone CLI for evaluating viral readiness of a single video or catalog JSON."""
    parser = argparse.ArgumentParser(description="Analyze short-form video viral readiness via FFmpeg")
    parser.add_argument("--file", help="Path to a single .mp4 file")
    parser.add_argument("--catalog", help="Path to catalog.json to score all entries")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not _check_ffmpeg_available():
        raise FFmpegNotFoundError()

    if args.file:
        rep = analyze_viral_readiness(args.file)
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            log.info(
                "[%s | %d/100] %s │ %s │ %.1fs │ hook=%sdB vs full=%sdB │ cpm=%.1f │ black=%s",
                rep["grade"], rep["score"], rep.get("file_name", args.file),
                rep.get("resolution", "?"), rep.get("duration_s", 0),
                rep.get("hook_3s_mean_db"), rep.get("overall_mean_db"),
                rep.get("cuts_per_minute", 0), rep.get("opening_blackframe", False),
            )
            for rec in rep.get("recommendations", []):
                log.info("  -> %s", rec)
        return

    if args.catalog:
        items = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
        reports = []
        log.info("═" * 78)
        log.info("  VIRAL READINESS SCORECARD (%d SHORTS)", len(items))
        log.info("═" * 78)
        for idx, entry in enumerate(items, 1):
            rep = analyze_viral_readiness(entry.get("video_path", ""))
            rep["id"] = entry.get("id")
            reports.append(rep)
            log.info(
                "  [%02d] %s (%3d/100) │ %-36s │ %.1fs │ hook=%sdB │ cpm=%4.1f",
                idx, rep["grade"], rep["score"], entry.get("id", "?"),
                rep.get("duration_s", 0), rep.get("hook_3s_mean_db"), rep.get("cuts_per_minute", 0),
            )
        if args.json:
            print(json.dumps(reports, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
