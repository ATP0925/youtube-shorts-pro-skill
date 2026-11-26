"""
Daily Automated Google AI & Procedural Video Producer (Veo + Gemini Flash + Endless Fallback).

Checks pending unuploaded Shorts in ``catalog_path`` and automatically generates
new 9:16 copyright-free Shorts using a resilient two-tier engine:
  1. Primary (Google Veo AI): Gemini Text (``gemini-2.5-flash``) + Google Veo
     (``veo-3.0-generate-preview`` / ``veo-2.0-generate-001``) 9:16 video
     when ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY`` is configured.
  2. Autonomous Fallback (Endless PD/Procedural): Automatically renders the next
     unused high-RPM topic (``cf_15``..``cf_28``) via NASA/Openverse/Wikimedia PD
     and 60FPS procedural graphics + Edge-TTS + ``-14 LUFS`` so scheduled slots
     never run dry even without paid API billing.
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
from copyright_free_shorts_factory import (
    _probe_audio_duration,
    _safe_shorts_title,
    _synthesize_edge_tts,
    build_topic_short,
)
from logger import get_logger
from media_loudness_validator import _check_ffmpeg_available, check_audio_loudness, probe_video

log = get_logger(__name__)

VEO_MODELS = ("veo-3.0-generate-preview", "veo-2.0-generate-001")
TEXT_MODELS = ("gemini-2.5-flash", "gemini-3.5-flash")

CATEGORY_ROTATION = [
    ("Space & Science Mysteries", "Science and technology", "28", "en-US-AndrewNeural"),
    ("Optical Illusions & Brain Games", "Entertainment", "24", "en-US-AvaNeural"),
    ("Food Science & Culinary Secrets", "How-to and style", "26", "en-US-EmmaNeural"),
    ("Human Body & Dark Psychology", "Education", "27", "en-US-BrianNeural"),
    ("AI, Tech & Hidden Secrets", "Science and technology", "28", "en-US-ChristopherNeural"),
    ("Weird History & World Mysteries", "Education", "27", "en-US-AndrewNeural"),
    ("Wealth Math & Money Paradoxes", "Education", "27", "en-US-GuyNeural"),
]

# Endless built-in expansion topics (used automatically if GEMINI_API_KEY/Veo is unset)
ENDLESS_FALLBACK_TOPICS: list[dict[str, Any]] = [
    {
        "id": "cf_15_space_diamond_rain",
        "category_key": "space_science",
        "yt_category": "Science and technology",
        "yt_category_id": "28",
        "playlist_name": "Space & Science Mysteries",
        "voice": "en-US-AndrewNeural",
        "accent": (0, 212, 255),
        "bg_rgb": (6, 12, 34),
        "badge": "COSMIC WEATHER",
        "hook_title": "IT LITERALLY RAINS DIAMONDS ON NEPTUNE",
        "hook_sub": "Extreme pressure turns methane gas into pure gems",
        "title": "Why It Rains Real Diamonds On Neptune & Uranus! #Shorts",
        "script": (
            "Forget rainstorms on Earth — inside Neptune and Uranus, real diamonds pour from the sky. "
            "Thousands of kilometers below turquoise clouds, crushing pressure splits methane gas into carbon atoms. "
            "Those carbon flakes squeeze into solid diamonds that sink toward the planetary core like glowing hail. "
            "Scientists recreated this inside laser labs on Earth and watched nano diamonds form in fractions. "
            "Subscribe for tomorrow's wild cosmic weather drop."
        ),
        "media_source": {"type": "nasa", "query": "neptune voyager blue planet rings"},
        "stages": [
            ("METHANE CLOUDS", "Rich carbon atmosphere deep inside ice giants"),
            ("10,000+ MPH CRUSH", "Extreme heat & pressure split hydrocarbon bonds"),
            ("SOLID DIAMOND HAIL", "Gemstone showers rain toward planetary core"),
            ("LAB CONFIRMED!", "Laser shock tests verified diamond formation"),
        ],
        "tags": ["diamond rain", "neptune facts", "nasa space", "planet mysteries", "astrophysics", "shorts"],
        "pinned_comment": "If humans could mine one planet in our solar system first, which would you pick?",
    },
    {
        "id": "cf_16_illusion_peripheral_fade",
        "category_key": "optical_illusion",
        "yt_category": "Entertainment",
        "yt_category_id": "24",
        "playlist_name": "Optical Illusions & Brain Games",
        "voice": "en-US-AvaNeural",
        "accent": (255, 45, 160),
        "bg_rgb": (14, 12, 22),
        "badge": "PERIPHERAL TRICK",
        "hook_title": "STARE AT THE DOT — COLORS ERASE THEMSELVES",
        "hook_sub": "Troxler fading shuts down static vision automatically",
        "title": "Watch Your Brain Delete Still Objects Live! #Shorts",
        "script": (
            "Keep both eyes frozen on the bright center dot and notice what happens around the border. "
            "Within seconds, every stationary shadow outside your focal point begins dissolving into fog. "
            "Neuroscientists call this Troxler fading — your brain ignores unmoving details to save energy. "
            "Now blink once! The entire hidden pattern snaps back instantly. "
            "Share this test with a friend to glitch their eyes too."
        ),
        "media_source": {"type": "procedural_illusion"},
        "stages": [
            ("FREEZE YOUR GAZE", "Keep eyes dead still on center dot"),
            ("TROXLER FADING", "Visual cortex filters out unmoving signals"),
            ("KEEP STARING...", "Retinal adaptation peaks in final seconds"),
            ("BLINK TO RESET!", "Did the pattern vanish then snap back?"),
        ],
        "tags": ["troxler effect", "optical illusion", "eye trick", "neuroscience", "brain test", "shorts"],
        "pinned_comment": "Honest result — did the outer rings fade or shift before blinking?",
    },
    {
        "id": "cf_17_food_pineapple_eats_you",
        "category_key": "food_science",
        "yt_category": "How-to and style",
        "yt_category_id": "26",
        "playlist_name": "Food Science & Culinary Secrets",
        "voice": "en-US-EmmaNeural",
        "accent": (255, 195, 0),
        "bg_rgb": (24, 14, 6),
        "badge": "FOOD ENZYMES",
        "hook_title": "WHY FRESH PINEAPPLE ACTUALLY DIGESTS YOUR TONGUE",
        "hook_sub": "That tingling sting is a real protein-eating enzyme",
        "title": "Why Pineapple Bites Your Tongue Back (Science)! #Shorts",
        "script": (
            "Ever wonder why your tongue tingles or feels raw after eating fresh slices of pineapple? "
            "It is not just acid — pineapple contains bromelain, an active enzyme that breaks down proteins. "
            "Chefs even use raw pineapple juice as a tenderizer because it literally dissolves tough steak fibers. "
            "Thankfully your stomach acid destroys bromelain right after swallowing and your tongue heals overnight. "
            "Sprinkle a pinch of salt to stop the sting instantly."
        ),
        "media_source": {"type": "openverse", "query": "fresh yellow pineapple fruit"},
        "stages": [
            ("BROMELAIN ENZYME", "Natural protease hidden in raw fruit"),
            ("MEAT TENDERIZER", "Chefs use it to break down muscle tissue"),
            ("TONGUE TINGLE", "Gently dissolves surface mouth proteins"),
            ("PINCH OF SALT", "Deactivates sting so flavor shines clean"),
        ],
        "tags": ["pineapple facts", "food science", "bromelain", "kitchen hack", "nutrition", "shorts"],
        "pinned_comment": "Did you know salt stops pineapple tongue burn instantly? Try it next time!",
    },
    {
        "id": "cf_18_body_liver_regrowth",
        "category_key": "psychology_body",
        "yt_category": "Education",
        "yt_category_id": "27",
        "playlist_name": "Human Body & Dark Psychology",
        "voice": "en-US-BrianNeural",
        "accent": (0, 255, 155),
        "bg_rgb": (8, 20, 22),
        "badge": "HUMAN SUPERPOWER",
        "hook_title": "THE ONLY HUMAN ORGAN THAT GROWS BACK WHOLE",
        "hook_sub": "Lose 70% and it rebuilds full functional mass",
        "title": "The Human Organ That Regrows Like A Superhero! #Shorts",
        "script": (
            "Most people think only lizards regrow lost body parts, yet humans carry one regenerating organ. "
            "Surgeons can remove up to seventy percent of your liver during life-saving donor transplants. "
            "Within just weeks, surviving hepatocytes multiply rapidly until original mass returns cleanly. "
            "Both the donor and patient end up with full-sized working livers from a single organ. "
            "Your biology carries built-in sci-fi recovery tools."
        ),
        "media_source": {"type": "openverse", "query": "human anatomy biology microscope cells"},
        "stages": [
            ("UP TO 70% REMOVED", "Safe partial living donor threshold"),
            ("RAPID CELL DIVISION", "Remaining tissue switches to growth mode"),
            ("WEEKS NOT YEARS", "Reaches near full metabolic capacity fast"),
            ("100% REBUILT!", "Nature's hidden human regeneration engine"),
        ],
        "tags": ["human body", "liver regeneration", "biology shorts", "medical facts", "anatomy", "shorts"],
        "pinned_comment": "Which human body fact amazed you most so far on CurioPulse?",
    },
    {
        "id": "cf_19_tech_voyager_memory",
        "category_key": "tech_ai",
        "yt_category": "Science and technology",
        "yt_category_id": "28",
        "playlist_name": "AI, Tech & Hidden Secrets",
        "voice": "en-US-ChristopherNeural",
        "accent": (75, 175, 255),
        "bg_rgb": (6, 14, 30),
        "badge": "DEEP SPACE TECH",
        "hook_title": "YOUR WATCH HAS MORE POWER THAN VOYAGER 1",
        "hook_sub": "Navigating interstellar space with 69 kilobytes of RAM",
        "title": "Voyager 1 Flies Past Our Solar System On 69KB RAM! #Shorts",
        "script": (
            "Right now, Voyager one races through interstellar space twenty four billion kilometers away. "
            "Its total onboard memory holds just sixty nine kilobytes — less than a single tiny phone photo. "
            "Engineers even use eight-track magnetic tape drives built back in the nineteen seventies to log data. "
            "Radio commands take twenty two hours one way, yet NASA still patches code cleanly fifty years later. "
            "Clean engineering always beats bloated hardware."
        ),
        "media_source": {"type": "procedural_gps"},
        "stages": [
            ("24 BILLION KM OUT", "Longest surviving deep-space messenger"),
            ("69 KB TOTAL RAM", "300,000x smaller than a modern smartphone"),
            ("44-HR ROUND TRIP", "Signal delay at speed of light both ways"),
            ("STILL ACTIVE!", "1977 computers still sending cosmic data"),
        ],
        "tags": ["voyager 1", "nasa tech", "retro computing", "space engineering", "tech shorts", "shorts"],
        "pinned_comment": "Crazy to think 69KB explored interstellar space while modern apps need gigabytes!",
    },
    {
        "id": "cf_20_history_oxford_vs_aztec",
        "category_key": "weird_history",
        "yt_category": "Education",
        "yt_category_id": "27",
        "playlist_name": "Weird History & World Mysteries",
        "voice": "en-US-AndrewNeural",
        "accent": (255, 140, 60),
        "bg_rgb": (24, 16, 12),
        "badge": "HISTORY WARP",
        "hook_title": "OXFORD UNIVERSITY IS OLDER THAN THE AZTEC EMPIRE",
        "hook_sub": "Students studied in England 300 years before Tenochtitlan",
        "title": "Oxford University Existed Before The Aztec Empire! #Shorts",
        "script": (
            "The Aztec Empire feels timelessly ancient, yet Oxford University beats it by more than three centuries. "
            "Teaching at Oxford was already active by the year ten ninety six in England. "
            "Meanwhile the Aztec capital Tenochtitlan was not founded until thirteen twenty five across the Atlantic. "
            "Generation after generation graduated from Oxford long before the first Aztec temple stone was laid. "
            "History timelines always play tricks on human memory."
        ),
        "media_source": {"type": "procedural_cleopatra_timeline"},
        "stages": [
            ("1096 CE: OXFORD", "Scholars already lecturing in England"),
            ("229 YRS PASS...", "Over two centuries of campus history"),
            ("1325 CE: AZTECS", "Tenochtitlan rises in Lake Texcoco"),
            ("TIMELINE SHOCK!", "Older than empires we call ancient"),
        ],
        "tags": ["weird history", "oxford university", "aztec empire", "history timeline", "facts", "shorts"],
        "pinned_comment": "Did you expect Oxford to be centuries older than the Aztec Empire? Yes or No!",
    },
    {
        "id": "cf_21_wealth_latte_compound",
        "category_key": "wealth_math",
        "yt_category": "Education",
        "yt_category_id": "27",
        "playlist_name": "Wealth Math & Money Paradoxes",
        "voice": "en-US-GuyNeural",
        "accent": (50, 235, 120),
        "bg_rgb": (6, 22, 14),
        "badge": "WEALTH MATH",
        "hook_title": "$10 DAILY HABIT EQUALS $1.7 MILLION OVER TIME",
        "hook_sub": "Small daily leaks compound faster than one big raise",
        "title": "How $10 A Day Silently Grows Into $1.7 Million! #Shorts",
        "script": (
            "Ten dollars a day sounds tiny until compounding turns pocket change into real freedom. "
            "Invest three hundred dollars every month at an average ten percent historical market pace. "
            "After ten years you hold sixty thousand, yet after thirty years it climbs past six hundred eighty grand. "
            "Push ten more years and time alone launches that exact ten dollar habit past one point seven million. "
            "Start early — time matters more than size."
        ),
        "media_source": {"type": "procedural_rule_72"},
        "stages": [
            ("$10 / DAY = $300/MO", "Less than daily impulse coffee & snacks"),
            ("YR 10 -> $61K", "Compound curve just warming up gently"),
            ("YR 30 -> $683K", "Interest earns more than your paycheck"),
            ("YR 40 -> $1.74M!", "Time turns tiny habits into wealth"),
        ],
        "tags": ["wealth math", "compound interest", "investing", "money habits", "finance shorts", "shorts"],
        "pinned_comment": "What small $5-$10 daily habit is easiest to redirect toward investing?",
    },
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


def _build_veo_entry(client: Any, catalog: list[dict[str, Any]], out_dir: Path, slot: str) -> dict[str, Any]:
    """Generate and validate one Google Veo AI Short entry."""
    used_titles = [e.get("youtube_shorts", {}).get("title", "") for e in catalog]
    plan = _plan_topic_with_gemini(client, used_titles, slot=slot, cat_idx=len(catalog))
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tid = f"veo_{stamp}_{slot}"
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

    tags = plan.get("tags", ["curiopulse", "science facts", "shorts"])
    desc = (
        f"{plan['hook_overlay']}\n\n{plan['script']}\n\n"
        f"#{' #'.join(t.replace(' ', '') for t in tags[:6])} #Shorts"
    )
    return {
        "id": tid,
        "slot": slot,
        "video_path": str(final_mp4.resolve()),
        "preview_path": str(preview_jpg.resolve()),
        "duration_s": dur_s,
        "generated_at": datetime.datetime.now().isoformat(),
        "source_engine": "google_veo",
        "youtube_shorts": {
            "title": _safe_shorts_title(plan["title"]),
            "description": desc,
            "tags": tags,
            "category": plan["yt_category"],
            "category_id": plan["yt_category_id"],
            "playlist_name": plan["playlist_name"],
            "altered_content": True,
            "pinned_comment": plan["pinned_comment"],
        },
    }


def _produce_endless_fallback_entry(
    catalog: list[dict[str, Any]],
    out_dir: Path,
    slot: str,
    fps: int = 24,
) -> dict[str, Any] | None:
    """Build next unused expansion topic using NASA/PD/Procedural 60FPS engine."""
    existing_ids = {e.get("id") for e in catalog}
    next_topic = next((t for t in ENDLESS_FALLBACK_TOPICS if t["id"] not in existing_ids), None)
    if next_topic is None:
        log.info("All built-in expansion topics already queued; awaiting GEMINI_API_KEY for infinite Veo AI.")
        return None
    entry = build_topic_short(next_topic, out_dir, fps=fps)
    entry["slot"] = slot
    entry["source_engine"] = "endless_procedural_pd"
    return entry


def produce_daily_veo_short(
    slot: str = "morning",
    force: bool = False,
    min_queue: int = 6,
    allow_fallback: bool = True,
) -> dict[str, Any] | None:
    """Ensure healthy unuploaded queue via Google Veo or endless PD/procedural fallback."""
    cfg = load_config()
    cat_path = Path(cfg["catalog_path"])
    catalog: list[dict[str, Any]] = load_json(cat_path, [])
    history: dict[str, Any] = load_json(cfg["history_path"], {"uploads": []})
    uploaded_ids = {u["id"] for u in history.get("uploads", []) if u.get("status") == "SUCCESS"}
    pending = [e for e in catalog if e.get("id") not in uploaded_ids and Path(e.get("video_path", "")).exists()]

    if not force and len(pending) >= min_queue:
        log.info("Queue healthy (%d pending >= %d). Skipping new generation today.", len(pending), min_queue)
        return None

    if not _check_ffmpeg_available():
        log.error("FFmpeg not available for daily Short generation.")
        return None

    out_dir = cat_path.resolve().parent / "copyright_free"
    entry: dict[str, Any] | None = None
    api_key = _resolve_gemini_api_key()

    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            entry = _build_veo_entry(client, catalog, out_dir, slot=slot)
        except Exception as exc:
            log.warning("Google Veo generation fallback triggered: %s", exc)

    if entry is None and allow_fallback:
        log.info("Rendering next endless copyright-free Short (%s slot) via NASA/PD/procedural engine...", slot)
        entry = _produce_endless_fallback_entry(catalog, out_dir, slot=slot, fps=24)

    if entry is None:
        return None

    pr = probe_video(entry["video_path"])
    ld = check_audio_loudness(entry["video_path"])
    if pr.get("error") or not (pr.get("is_9_16") and pr.get("under_60s")) or not ld.get("ok"):
        log.error("Newly generated Short failed media/loudness verification: %s", entry["id"])
        return None

    catalog.append(entry)
    save_json(cat_path, catalog)
    log.info(
        "Appended verified Short [%s] → %s (%s, %.1fs, mean=%s dB)",
        entry.get("source_engine", "factory"),
        entry["id"],
        entry["youtube_shorts"]["title"],
        pr.get("duration", 0),
        ld.get("mean_db"),
    )
    return entry


def main() -> None:
    """CLI entry point for automated daily Google Veo / Procedural Shorts replenishment."""
    parser = argparse.ArgumentParser(description="Daily automated Google Veo & endless Shorts producer")
    parser.add_argument("--slot", choices=["morning", "night"], default="morning")
    parser.add_argument("--min-queue", type=int, default=6, help="Generate new Short if pending < min-queue")
    parser.add_argument("--force", action="store_true", help="Force generating one new Short right now")
    parser.add_argument("--no-fallback", action="store_true", help="Require live Google Veo only")
    args = parser.parse_args()

    try:
        produce_daily_veo_short(
            slot=args.slot,
            force=args.force,
            min_queue=args.min_queue,
            allow_fallback=not args.no_fallback,
        )
    except Exception as exc:
        log.warning("Daily producer non-fatal note: %s", exc)
        sys.exit(0)


if __name__ == "__main__":
    main()
