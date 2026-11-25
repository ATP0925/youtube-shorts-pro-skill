"""
Media, Audio Loudness (FFmpeg volumedetect) & Pro Metadata Readiness Validator
------------------------------------------------------------------------------
Validates 9:16 vertical aspect ratio, duration <= 60s, AAC/audio stream presence,
healthy broadcast loudness (-38 dBFS to -3 dBFS), and complete SEO/YPP fields.
"""

import json
import os
import subprocess
from typing import Any, Dict


def probe_video(video_path: str) -> Dict[str, Any]:
    """Inspect video file with ffprobe for resolution, duration, and audio stream."""
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

        return {
            "width": w,
            "height": h,
            "duration": round(dur, 2),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "has_audio": has_audio,
            "video_codec": vstream.get("codec_name", "unknown"),
            "is_9_16": (w == 1080 and h == 1920) or (h > 0 and abs((w / h) - (9 / 16)) < 0.01),
            "under_60s": dur <= 60.0,
            "error": None,
        }
    except Exception as e:
        return {"error": f"FFprobe failed: {e}"}


def check_audio_loudness(video_path: str) -> Dict[str, Any]:
    """Measure mean & max volume via FFmpeg volumedetect (non-silent, non-clipping guard)."""
    if not os.path.exists(video_path):
        return {"ok": False, "mean_db": None, "max_db": None, "error": "file missing"}
    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    cmd = ["ffmpeg", "-hide_banner", "-i", video_path, "-af", "volumedetect", "-f", "null", null_sink]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
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
        ok = mean_db is not None and -38.0 <= mean_db <= -3.0
        return {"ok": ok, "mean_db": mean_db, "max_db": max_db, "error": None}
    except Exception as e:
        return {"ok": False, "mean_db": None, "max_db": None, "error": str(e)}


def verify_catalog_items(catalog: list[dict], check_loudness: bool = True) -> bool:
    """Validate every queued Short against resolution, duration, loudness, and pro metadata rules."""
    if not catalog:
        print("[ERROR] Catalog is empty.")
        return False

    print(f"=== AUDITING {len(catalog)} YOUTUBE SHORTS (MEDIA + LOUDNESS + METADATA) ===")
    all_ok = True
    for idx, entry in enumerate(catalog, 1):
        eid = entry.get("id", f"item_{idx}")
        vpath = entry.get("video_path", "")
        yt = entry.get("youtube_shorts", {})
        title = yt.get("title", "")

        pr = probe_video(vpath)
        if pr.get("error"):
            print(f"  [{idx:02d}] FAIL | {eid} | {pr['error']}")
            all_ok = False
            continue

        loud_ok = True
        mean_str = "n/a"
        if check_loudness and pr.get("has_audio"):
            ld = check_audio_loudness(vpath)
            loud_ok = ld.get("ok", False)
            if ld.get("mean_db") is not None:
                mean_str = f"{ld['mean_db']:>5.1f}dB"

        title_ok = len(title) <= 60 and "#Shorts" in title
        meta_ok = bool(yt.get("game_title") and yt.get("playlist_name") and yt.get("pinned_comment"))
        ok = pr["is_9_16"] and pr["under_60s"] and pr["has_audio"] and loud_ok and title_ok and meta_ok
        if not ok:
            all_ok = False

        print(
            f"  [{idx:02d}] {'PASS' if ok else 'FAIL'} | {eid:<36s} | {pr['width']}x{pr['height']} | "
            f"{pr['duration']:>5.1f}s | {mean_str} | meta={'OK' if meta_ok else 'MISS'} | title={len(title)}c"
        )
    return all_ok
