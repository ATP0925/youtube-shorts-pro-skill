"""
Daily Automated Google AI Video Producer (Veo + Gemini Flash + Neural VO).

Checks pending unuploaded Shorts in ``catalog_path`` and automatically generates
new 9:16 copyright-free Shorts using:
  1. Gemini Text (``gemini-2.5-flash``) for novel high-retention script & metadata
  2. Google Veo (``veo-3.0-generate-preview`` / ``veo-2.0-generate-001``) for 9:16
     original AI motion footage when ``GEMINI_API_KEY`` (or ``GOOGLE_API_KEY``) is set
  3. Neural voiceover (``edge-tts`` WordBoundary) + kinetic ASS captions + FFmpeg
     ``-14 LUFS`` loudness normalization.

If no API key or Veo quota is available, logs cleanly and exits 0 so scheduled
uploads continue using existing curated/procedural queue items without interruption.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_subtitle_styler import build_ass_from_segments
from config_loader import load_config, load_json, save_json
from constants import (
    SHORTS_ASPECT_HEIGHT,
    SHORTS_ASPECT_WIDTH,
    TARGET_LOUDNORM_I,
    TARGET_LOUDNORM_LRA,
    TARGET_LOUDNORM_TP,
)
from copyright_free_shorts_factory import _probe_audio_duration, _safe_shorts_title, _synthesize_edge_tts
from logger import get_logger
from media_loudness_validator import _check_ffmpeg_available

log = get_logger(__name__)

VEO_MODELS = ("veo-3.0-generate-preview", "veo-2.0-generate-001")
TEXT_MODELS = ("gemini-2.5-flash", "gemini-3.5-flash")

CATEGORY_ROTATION = [
    ("Space & Science Mysteries", "Science & Technology", "28", "en-US-AndrewNeural"),
    ("Optical Illusions & Brain Games", "Entertainment", "24", "en-US-AvaNeural"),
    ("Food Science & Culinary Secrets", "Howto & Style", "26", "en-US-EmmaNeural"),
    ("Human Body & Dark Psychology", "Education", "27", "en-US-BrianNeural"),
    ("AI, Tech & Hidden Secrets", "Science & Technology", "28", "en-US-ChristopherNeural"),
    ("Weird History & World Mysteries", "Education", "27", "en-US-AndrewNeural"),
    ("Wealth Math & Money Paradoxes", "Education", "27", "en-US-GuyNeural"),
]


def _resolve_gemini_api_key() -> str | None:
    """Resolve GEMINI_API_KEY / GOOGLE_API_KEY from environment or YT_PRO_HOME/.env."""
    for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(env_name, "").strip()
        if val:
            return val
    cfg = load_config()
    for base in {Path(cfg.get("catalog_path", ".")).resolve().parent.parent, Path.cwd()}:
        env_file = base / ".env"
        if env_file.exists():
            try:
                from dotenv import dotenv_values
                vals = dotenv_values(env_file)
                for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                    if vals.get(env_name):
                        return str(vals[env_name]).strip()
            except Exception:
                pass
    return None


def _plan_topic_with_gemini(client: Any, used_titles: list[str], slot: str, cat_idx: int) -> dict[str, Any]:
    """Generate a structured, non-duplicate viral curiosity Short plan using Gemini Flash."""
    playlist, yt_cat, cat_id, voice = CATEGORY_ROTATION[cat_idx % len(CATEGORY_ROTATION)]
    avoid = "; ".join(used_titles[-15:]) if used_titles else "none"
    prompt = (
        f"Create 1 brand-new viral YouTube Short concept for the category '{playlist}'.\n"
        f"Avoid repeating these existing titles: [{avoid}].\n"
        "Return strict JSON with keys:\n"
        '  "title": engaging <=52 char title ending with " #Shorts",\n'
        '  "hook_overlay": short 3-6 word ALL CAPS top banner hook,\n'
        '  "script": 60-72 word punchy US English curiosity narration with a surprising 2nd-sentence twist,\n'
        '  "veo_prompt": rich vertical 9:16 cinematic 3D/scientific visualization video prompt '
        "(zero readable text inside video, vibrant lighting, smooth slow motion),\n"
        '  "tags": list of 8 concise SEO keyword strings,\n'
        '  "pinned_comment": engaging 1-sentence question for viewers.\n'
    )
    last_err: Exception | None = None
    for tm in TEXT_MODELS:
        try:
            resp = client.models.generate_content(
                model=tm,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(resp.text)
            data.update({
                "playlist_name": playlist,
                "yt_category": yt_cat,
                "yt_category_id": cat_id,
                "voice": voice,
                "slot": slot,
            })
            return data
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Gemini topic planning failed: {last_err}")


def _generate_veo_clip(client: Any, veo_prompt: str, out_raw_mp4: Path, timeout_s: int = 240) -> Path:
    """Call Google Veo to generate an original vertical 9:16 clip and download it."""
    from google.genai import types

    last_err: Exception | None = None
    for model_id in VEO_MODELS:
        try:
            log.info("Requesting Google Veo 9:16 video (%s)...", model_id)
            op = client.models.generate_videos(
                model=model_id,
                prompt=veo_prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",
                    number_of_videos=1,
                    person_generation="allow_adult",
                ),
            )
            deadline = time.time() + timeout_s
            while not op.done:
                if time.time() > deadline:
                    raise TimeoutError(f"Veo generation timed out after {timeout_s}s")
                time.sleep(8)
                op = client.operations.get(op)
            vids = getattr(getattr(op, "response", None), "generated_videos", None) or []
            if not vids:
                raise RuntimeError(f"Veo operation completed with no videos ({model_id})")
            client.files.download(file=vids[0].video)
            out_raw_mp4.parent.mkdir(parents=True, exist_ok=True)
            vids[0].video.save(str(out_raw_mp4))
            log.info("Google Veo clip downloaded → %s", out_raw_mp4)
            return out_raw_mp4
        except Exception as exc:
            last_err = exc
            log.warning("Veo model %s note: %s", model_id, exc)
    raise RuntimeError(f"All Veo models failed: {last_err}")


def produce_daily_veo_short(slot: str = "morning", force: bool = False, min_queue: int = 6) -> dict[str, Any] | None:
    """Ensure healthy unuploaded queue and build one Google Veo AI Short when configured."""
    cfg = load_config()
    cat_path = Path(cfg["catalog_path"])
    catalog: list[dict[str, Any]] = load_json(cat_path, [])
    history: dict[str, Any] = load_json(cfg["history_path"], {"uploads": []})
    uploaded_ids = {u["id"] for u in history.get("uploads", []) if u.get("status") == "SUCCESS"}
    pending = [e for e in catalog if e.get("id") not in uploaded_ids and Path(e.get("video_path", "")).exists()]

    if not force and len(pending) >= min_queue:
        log.info("Queue healthy (%d pending >= %d). Skipping Veo generation today.", len(pending), min_queue)
        return None

    api_key = _resolve_gemini_api_key()
    if not api_key:
        log.info(
            "GEMINI_API_KEY not set — automated Google Veo generator waiting on API key "
            "(pending local queue=%d).",
            len(pending),
        )
        return None

    if not _check_ffmpeg_available():
        log.error("FFmpeg not available for Veo post-production.")
        return None

    from google import genai

    client = genai.Client(api_key=api_key)
    used_titles = [e.get("youtube_shorts", {}).get("title", "") for e in catalog]
    plan = _plan_topic_with_gemini(client, used_titles, slot=slot, cat_idx=len(catalog))

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tid = f"veo_{stamp}_{slot}"
    out_dir = Path(cfg["catalog_path"]).resolve().parent / "copyright_free"
    work_dir = out_dir / "_work" / tid
    work_dir.mkdir(parents=True, exist_ok=True)

    raw_veo = work_dir / f"{tid}_raw.mp4"
    voice_mp3 = work_dir / f"{tid}_voice.mp3"
    ass_path = work_dir / f"{tid}.ass"
    final_mp4 = out_dir / f"{tid}.mp4"
    preview_jpg = out_dir / f"preview_{tid}.jpg"

    _generate_veo_clip(client, plan["veo_prompt"], raw_veo)
    chunks = asyncio.run(_synthesize_edge_tts(plan["script"], plan["voice"], voice_mp3))
    dur_s = min(55.0, round(_probe_audio_duration(voice_mp3) + 0.8, 2))
    build_ass_from_segments(chunks, ass_path, font_name="Segoe UI Black", font_size=60)

    ass_esc = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    ambient_expr = (
        "aevalsrc='0.028*sin(2*PI*110*t)+0.018*sin(2*PI*165*t)"
        "+0.012*sin(2*PI*220*t)*sin(2*PI*0.25*t)':s=44100:c=stereo"
    )
    hook_txt = plan["hook_overlay"].replace("'", "").replace(":", " ")[:48]
    fc = (
        f"[0:v]scale={SHORTS_ASPECT_WIDTH}:{SHORTS_ASPECT_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={SHORTS_ASPECT_WIDTH}:{SHORTS_ASPECT_HEIGHT},fps=30,"
        f"drawtext=text='{hook_txt}':x=(w-text_w)/2:y=220:fontsize=46:fontcolor=white:"
        f"box=1:boxcolor=0x0A0C1AE0:boxborderw=22,ass='{ass_esc}'[vout];"
        f"{ambient_expr},atrim=0:{dur_s},lowpass=f=480[bed];"
        f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad=whole_dur={dur_s}[vo];"
        f"[vo][bed]amix=inputs=2:duration=first:weights=1.0 0.35,"
        f"loudnorm=I={TARGET_LOUDNORM_I}:LRA={TARGET_LOUDNORM_LRA}:tp={TARGET_LOUDNORM_TP}[aout]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(raw_veo),
        "-i", str(voice_mp3),
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(dur_s),
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(final_mp4),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0 or not final_mp4.exists():
        raise RuntimeError(f"Veo FFmpeg merge failed: {(res.stderr or '')[-500:]}")

    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(round(dur_s * 0.5, 2)), "-i", str(final_mp4), "-vframes", "1", str(preview_jpg)],
        capture_output=True,
    )

    title = _safe_shorts_title(plan["title"])
    tags = plan.get("tags", ["curiopulse", "science facts", "shorts"])
    desc = (
        f"{plan['hook_overlay']}\n\n{plan['script']}\n\n"
        f"#{' #'.join(t.replace(' ', '') for t in tags[:6])} #Shorts"
    )
    entry: dict[str, Any] = {
        "id": tid,
        "slot": slot,
        "video_path": str(final_mp4.resolve()),
        "preview_path": str(preview_jpg.resolve()),
        "duration_s": dur_s,
        "generated_at": datetime.datetime.now().isoformat(),
        "source_engine": "google_veo",
        "youtube_shorts": {
            "title": title,
            "description": desc,
            "tags": tags,
            "category": plan["yt_category"],
            "category_id": plan["yt_category_id"],
            "playlist_name": plan["playlist_name"],
            "altered_content": True,
            "pinned_comment": plan["pinned_comment"],
        },
    }
    catalog.append(entry)
    save_json(cat_path, catalog)
    log.info("Appended new Google Veo Short to catalog → %s (%s)", tid, title)
    return entry


def main() -> None:
    """CLI entry point for automated daily Google Veo Shorts replenishment."""
    parser = argparse.ArgumentParser(description="Daily automated Google Veo AI Shorts producer")
    parser.add_argument("--slot", choices=["morning", "night"], default="morning")
    parser.add_argument("--min-queue", type=int, default=6, help="Generate new Veo Short if pending < min-queue")
    parser.add_argument("--force", action="store_true", help="Force generating a new Google Veo Short now")
    args = parser.parse_args()

    try:
        produce_daily_veo_short(slot=args.slot, force=args.force, min_queue=args.min_queue)
    except Exception as exc:
        log.warning("Veo producer non-fatal fallback note: %s", exc)
        sys.exit(0)


if __name__ == "__main__":
    main()
