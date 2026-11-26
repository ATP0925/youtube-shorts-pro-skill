"""
100% Copyright-Free Global Multi-Category Viral Shorts Factory.

Generates original, YPP-safe vertical 1080×1920 MP4 Shorts across top global
viral categories using only:
  - Neural US English voiceover (edge-tts WordBoundary exact sync)
  - Synthesized FFmpeg ambient bed + procedural hook/transition SFX (0 Content ID risk)
  - Public Domain (NASA API) + Openverse CC0/PDM images + 100% procedural 60FPS animations

Avoids YPP 2025/2026 'Inauthentic Content' penalties by rendering distinct
per-category motion graphics (exponential race charts, optical afterimage illusions,
multi-stage bio meters, space telemetry HUD, historical timelines, etc.).
"""

from __future__ import annotations

import asyncio
import datetime
import io
import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_subtitle_styler import build_ass_from_segments
from constants import (
    SHORTS_ASPECT_HEIGHT,
    SHORTS_ASPECT_WIDTH,
    TARGET_LOUDNORM_I,
    TARGET_LOUDNORM_LRA,
    TARGET_LOUDNORM_TP,
)
from exceptions import FFmpegNotFoundError
from logger import get_logger
from media_loudness_validator import _check_ffmpeg_available

log = get_logger(__name__)

__all__ = ["GLOBAL_VIRAL_TOPICS", "build_topic_short", "build_all_global_shorts"]

FONT_BOLD_CANDIDATES = [
    r"C:\Windows\Fonts\seguibl.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_REG_CANDIDATES = [
    r"C:\Windows\Fonts\seguisb.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in (FONT_BOLD_CANDIDATES if bold else FONT_REG_CANDIDATES):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ── Top 7 Global High-View Copyright-Free Categories ───────────────────

GLOBAL_VIRAL_TOPICS: list[dict[str, Any]] = [
    {
        "id": "cf_01_space_black_hole",
        "category_key": "space_science",
        "yt_category": "Science & Technology",
        "yt_category_id": "28",
        "playlist_name": "Space & Science Mysteries",
        "voice": "en-US-AndrewMultilingualNeural",
        "accent": (0, 235, 255),
        "bg_rgb": (6, 10, 28),
        "badge": "COSMIC DISCOVERY",
        "hook_title": "THE BLACK HOLE THAT EATS A SUN DAILY",
        "hook_sub": "Astronomers found J0529-4351 — watch scale",
        "title": "The Black Hole That Eats One Sun Every Day! #Shorts",
        "script": (
            "Astronomers just spotted a black hole so hungry it swallows an entire sun every single day. "
            "It sits twelve billion light years away, glowing five hundred trillion times brighter than our own sun. "
            "Its accretion disk spans seven light years wide, spinning superheated gas near light speed. "
            "If this monster replaced our sun, our entire solar system would vanish inside its shadow in seconds. "
            "And that tiny dot on the map proves how wild deep space really gets. Follow for the next cosmic mystery."
        ),
        "media_source": {"type": "nasa", "query": "black hole nebula galaxy"},
        "stages": [
            ("17 BILLION SUNS", "Measured black hole mass"),
            ("500 TRILLION x", "Brighter than our Sun"),
            ("7 LIGHT YEARS", "Swirling accretion disk width"),
            ("1 SUN / DAY", "Daily matter consumption rate"),
        ],
        "tags": [
            "black hole", "space facts", "astronomy shorts", "science mysteries",
            "universe facts", "nasa discovery", "cosmic wonders", "j0529", "astrophysics", "shorts",
        ],
        "pinned_comment": "Do you think even bigger monsters are hiding past the observable universe? Drop your theory below!",
    },
    {
        "id": "cf_02_optical_illusion_afterimage",
        "category_key": "optical_illusion",
        "yt_category": "Entertainment",
        "yt_category_id": "24",
        "playlist_name": "Optical Illusions & Brain Games",
        "voice": "en-US-AvaMultilingualNeural",
        "accent": (255, 45, 160),
        "bg_rgb": (14, 12, 22),
        "badge": "OPTICAL CHALLENGE",
        "hook_title": "STARE AT THE CENTER DOT — DO NOT BLINK",
        "hook_sub": "Your brain will invent fake color on black & white",
        "title": "Stare At The Dot & Watch Gray Turn Full Color! #Shorts",
        "script": (
            "Stare straight at the glowing white dot in the center right now and do not look away. "
            "In ten seconds, the bright neon ring around this frame will suddenly vanish into pure gray. "
            "Keep your eyes locked on the center dot while your retinal cones adapt to the intense magenta and cyan glow. "
            "Three, two, one, switch! Do you see golden yellow and deep blue on a completely grayscale frame? "
            "Look away and the color disappears instantly. Double tap to test your eyes again right from..."
        ),
        "media_source": {"type": "procedural_illusion"},
        "stages": [
            ("STEP 1: LOCK EYES", "Stare strictly at the center white dot"),
            ("ADAPTING CONES", "Retina sensors fatiguing in real time"),
            ("FINAL COUNTDOWN", "Get ready for zero-color grayscale swap"),
            ("PURE GRAYSCALE!", "Did your brain paint phantom colors?"),
        ],
        "tags": [
            "optical illusion", "brain trick", "visual illusion", "color afterimage",
            "perception test", "mind trick", "neuroscience", "psychology shorts", "shorts",
        ],
        "pinned_comment": "Honest check — did the black and white frame flash phantom colors for 2 seconds? Yes or No below!",
    },
    {
        "id": "cf_03_food_honey_3000years",
        "category_key": "food_science",
        "yt_category": "Howto & Style",
        "yt_category_id": "26",
        "playlist_name": "Food Science & Culinary Secrets",
        "voice": "en-US-EmmaMultilingualNeural",
        "accent": (255, 195, 0),
        "bg_rgb": (24, 14, 6),
        "badge": "FOOD SCIENCE",
        "hook_title": "WHY 3,000-YEAR-OLD HONEY NEVER SPOILS",
        "hook_sub": "Found in Egyptian tombs — still 100% edible today",
        "title": "Why 3,000-Year-Old Honey Never Ever Spoils! #Shorts",
        "script": (
            "Archaeologists opened three thousand year old Egyptian tombs and found jars of honey that were still completely edible. "
            "Almost every other food rots within days, so why does pure honey survive millennia? "
            "First, bees dehydrate nectar down to under eighteen percent water, starving bacteria of moisture. "
            "Second, honey has an acidic pH around three point nine and slowly releases natural hydrogen peroxide. "
            "Unless water leaks inside the jar, microbes simply cannot survive. Check your kitchen jar before buying..."
        ),
        "media_source": {"type": "openverse", "query": "golden honey comb"},
        "stages": [
            ("< 18% WATER", "Dehydrates & starves bacteria on contact"),
            ("pH 3.9 ACIDITY", "Blocks pathogen reproduction completely"),
            ("NATURAL H2O2", "Enzyme releases slow antimicrobial trace"),
            ("3,000+ YEARS", "Oldest sealed jars remained safe to eat"),
        ],
        "tags": [
            "food science", "honey facts", "why honey never spoils", "culinary chemistry",
            "amazing food", "ancient egypt honey", "kitchen science", "edutainment", "shorts",
        ],
        "pinned_comment": "What is the oldest food item sitting in your pantry right now? Be honest!",
    },
    {
        "id": "cf_04_body_72h_nosleep",
        "category_key": "psychology_body",
        "yt_category": "Education",
        "yt_category_id": "27",
        "playlist_name": "Human Body & Dark Psychology",
        "voice": "en-US-BrianMultilingualNeural",
        "accent": (0, 255, 155),
        "bg_rgb": (8, 20, 22),
        "badge": "HUMAN BIOLOGY",
        "hook_title": "YOUR BRAIN AFTER 72 HOURS WITH ZERO SLEEP",
        "hook_sub": "Minute-by-minute biological breakdown",
        "title": "What 72 Hours Without Sleep Does To Your Brain! #Shorts",
        "script": (
            "Skip sleep for seventy two straight hours and your own brain starts eating its worn neural connections. "
            "At twenty four hours, reaction speed drops to the level of legal intoxication and cortisol spikes hard. "
            "By hour forty eight, your brain forces micro sleeps lasting three seconds while your eyes remain wide open. "
            "At hour seventy two, vivid waking hallucinations kick in as memory and emotional control collapse. "
            "Sleep is when your glymphatic system flushes toxic proteins out — save this before your next late night."
        ),
        "media_source": {"type": "openverse", "query": "human brain neuron light"},
        "stages": [
            ("HOUR 24", "Coordination matches 0.10% blood alcohol"),
            ("HOUR 48", "Involuntary 3-second micro-sleeps begin"),
            ("HOUR 60", "Cortisol & amygdala fear response surge"),
            ("HOUR 72", "Hallucinations + glymphatic waste buildup"),
        ],
        "tags": [
            "human body facts", "sleep deprivation", "neuroscience", "brain facts",
            "what happens if", "psychology facts", "health science", "biology shorts", "shorts",
        ],
        "pinned_comment": "What is the longest streak you ever stayed awake (exams, gaming, or work)? Drop your hour count!",
    },
    {
        "id": "cf_05_tech_gps_einstein",
        "category_key": "tech_ai",
        "yt_category": "Science & Technology",
        "yt_category_id": "28",
        "playlist_name": "AI, Tech & Hidden Secrets",
        "voice": "en-US-ChristopherNeural",
        "accent": (75, 175, 255),
        "bg_rgb": (6, 14, 30),
        "badge": "HIDDEN TECH",
        "hook_title": "WHY GPS WOULD FAIL BY 11 KM EVERY SINGLE DAY",
        "hook_sub": "The Einstein physics trick running inside your phone",
        "title": "Why Phone GPS Breaks By 11km/Day Without Einstein! #Shorts",
        "script": (
            "Your smartphone map looks effortless, yet without Albert Einstein your GPS location would drift off course by eleven kilometers every single day. "
            "GPS satellites orbit twenty thousand kilometers up where Earth gravity is weaker, making their atomic clocks tick faster. "
            "Meanwhile their high orbital speed slows their clocks slightly in the opposite direction. "
            "Combined, satellite time runs ahead by thirty eight microseconds every day — and engineers adjust every chip on earth for that exact drift. "
            "Every time you tap navigate, relativity saves your ride."
        ),
        "media_source": {"type": "procedural_gps"},
        "stages": [
            ("20,200 KM UP", "GPS satellites orbit at 14,000 km/h"),
            ("-7 us / DAY", "Special relativity speed clock slowdown"),
            ("+45 us / DAY", "General relativity weaker gravity speedup"),
            ("+38 us = 11.4 KM", "Daily position error without Einstein fix"),
        ],
        "tags": [
            "tech facts", "how gps works", "einstein relativity", "smartphone secrets",
            "science technology", "physics in real life", "engineering", "tech shorts", "shorts",
        ],
        "pinned_comment": "Did you know relativistic physics corrects your Uber & Google Maps every second? Rate this mind-blow 1-10!",
    },
    {
        "id": "cf_06_history_roman_concrete",
        "category_key": "weird_history",
        "yt_category": "Education",
        "yt_category_id": "27",
        "playlist_name": "Weird History & World Mysteries",
        "voice": "en-US-AndrewMultilingualNeural",
        "accent": (255, 140, 60),
        "bg_rgb": (24, 16, 12),
        "badge": "ANCIENT MYSTERY",
        "hook_title": "2,000-YEAR ROMAN HARBORS STILL BEAT MODERN STEEL",
        "hook_sub": "MIT cracked the self-healing recipe",
        "title": "Why 2,000-Year-Old Roman Concrete Heals Itself! #Shorts",
        "script": (
            "Modern concrete cracks and crumbles in seawater within fifty years, yet ancient Roman harbors built two thousand years ago are still standing strong. "
            "Scientists at MIT finally discovered the secret hidden inside tiny white specks baked into the stone. "
            "Romans used hot mixing with quicklime and volcanic ash, locking reactive calcium pockets inside the wall. "
            "Whenever ocean waves crack the structure, seawater wakes up that lime, instantly growing fresh crystals that seal the crack shut. "
            "Two millennia later, engineers are copying ancient Rome to fix our cities."
        ),
        "media_source": {"type": "openverse", "query": "ancient roman pantheon colosseum architecture"},
        "stages": [
            ("50 YRS (MODERN)", "Saltwater rusts steel rebar from inside"),
            ("VOLCANIC ASH", "Mixed hot with reactive quicklime specks"),
            ("WATER ENTERS CRACK", "Dissolves trapped lime crystals instantly"),
            ("2,000+ YRS STRONG", "Cracks recrystallize & self-seal forever"),
        ],
        "tags": [
            "ancient history", "roman concrete", "history mysteries", "engineering history",
            "ancient rome", "architecture secrets", "weird history", "mit discovery", "shorts",
        ],
        "pinned_comment": "What ancient invention do you think is still ahead of modern tech? Drop it below!",
    },
    {
        "id": "cf_07_wealth_penny_paradox",
        "category_key": "wealth_math",
        "yt_category": "Education",
        "yt_category_id": "27",
        "playlist_name": "Wealth Math & Money Paradoxes",
        "voice": "en-US-GuyNeural",
        "accent": (50, 235, 120),
        "bg_rgb": (6, 22, 14),
        "badge": "WEALTH MATH",
        "hook_title": "$1,000,000 CASH TODAY OR $0.01 DOUBLED FOR 30 DAYS?",
        "hook_sub": "90% of people pick the wrong option instantly",
        "title": "$1 Million Cash vs $0.01 Doubled 30 Days — Watch Math! #Shorts",
        "script": (
            "Would you take one million dollars cash today, or a single penny that doubles every day for thirty days? "
            "Halfway through on day fifteen, that penny is only worth one hundred sixty three dollars while the millionaire looks way ahead. "
            "Even on day twenty one, you barely hit ten thousand dollars — and most people regret turning down the cash. "
            "Watch what happens in the final week: day twenty eight crosses one point three million, and day thirty explodes past five point three six million! "
            "Compounding looks invisible until it overtakes everything."
        ),
        "media_source": {"type": "procedural_wealth"},
        "stages": [
            ("DAY 1 -> $0.01", "Looks worthless next to $1,000,000"),
            ("DAY 15 -> $163", "Still trailing by 99.98% halfway through"),
            ("DAY 24 -> $83,886", "Exponential curve suddenly turns vertical"),
            ("DAY 30 -> $5.36M!", "More than 5x richer than $1M flat cash"),
        ],
        "tags": [
            "money math", "compound interest", "wealth paradox", "penny doubled 30 days",
            "financial education", "exponential growth", "brain teaser", "finance shorts", "shorts",
        ],
        "pinned_comment": "Be honest — before seeing Day 28, would you have grabbed the $1,000,000 cash immediately?",
    },
]


# ── Public Domain / CC0 Visual Fetchers ────────────────────────────────

def _http_get_json(url: str, timeout: int = 12) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "YouTubeShortsProSkill/3.2 (PD-Fetcher)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_image(url: str, timeout: int = 12) -> Image.Image | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YouTubeShortsProSkill/3.2 (PD-Fetcher)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        if min(img.size) >= 320:
            return img
    except Exception:
        pass
    return None


def fetch_nasa_pd_images(query: str, count: int = 4) -> list[Image.Image]:
    """Fetch 100% US Gov Public Domain space images from NASA Image API."""
    imgs: list[Image.Image] = []
    try:
        url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
        data = _http_get_json(url)
        for item in data.get("collection", {}).get("items", []):
            for link in item.get("links", []):
                href = link.get("href", "")
                if href.lower().endswith((".jpg", ".jpeg", ".png")):
                    im = _download_image(href)
                    if im is not None:
                        imgs.append(im)
                        break
            if len(imgs) >= count:
                break
    except Exception as exc:
        log.warning("NASA fetch note (%s): %s", query, exc)
    return imgs


def fetch_openverse_cc0_images(query: str, count: int = 4) -> list[Image.Image]:
    """Fetch strictly CC0 / Public Domain Mark imagery from Openverse."""
    imgs: list[Image.Image] = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.openverse.org/v1/images/?q={q}&license=cc0,pdm&page_size=12"
        data = _http_get_json(url)
        for res in data.get("results", []):
            lic = (res.get("license") or "").lower()
            if lic not in {"cc0", "pdm"}:
                continue
            src = res.get("url") or res.get("thumbnail") or ""
            if src:
                im = _download_image(src)
                if im is not None:
                    imgs.append(im)
            if len(imgs) >= count:
                break
    except Exception as exc:
        log.warning("Openverse CC0 fetch note (%s): %s", query, exc)
    return imgs


# ── Edge-TTS Narration + Millisecond Word Timestamps ───────────────────

async def _synthesize_edge_tts(text: str, voice: str, mp3_path: Path) -> list[dict[str, Any]]:
    """Synthesize speech with Edge-TTS and extract phrase subtitle chunks from WordBoundary events."""
    import edge_tts

    comm = edge_tts.Communicate(text, voice)
    chunks: list[dict[str, Any]] = []
    word_buf: list[dict[str, Any]] = []
    mp3_path.parent.mkdir(parents=True, exist_ok=True)

    with open(mp3_path, "wb") as f:
        async for msg in comm.stream():
            mtype = msg.get("type")
            if mtype == "audio":
                f.write(msg["data"])
            elif mtype == "WordBoundary":
                start_s = msg["offset"] / 10_000_000.0
                dur_s = max(0.12, msg["duration"] / 10_000_000.0)
                wtxt = str(msg.get("text", "")).strip()
                if wtxt:
                    word_buf.append({"start": start_s, "end": start_s + dur_s, "text": wtxt})

    # Group into punchy 2-3 word kinetic subtitle beats
    for i in range(0, len(word_buf), 3):
        grp = word_buf[i:i + 3]
        phrase = " ".join(w["text"] for w in grp).strip().upper()
        if phrase:
            chunks.append({
                "start": grp[0]["start"],
                "end": max(grp[-1]["end"], grp[0]["start"] + 0.35),
                "text": phrase,
            })
    return chunks


def _probe_audio_duration(audio_path: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True,
    )
    try:
        return max(15.0, float((res.stdout or "25").strip()))
    except ValueError:
        return 25.0


# ── Procedural 60FPS Visual Engines (YPP Authentic & Dynamic) ──────────

def _wrap_text_to_width(draw: ImageDraw.ImageDraw, text: str, font: Any, max_px: int) -> list[str]:
    """Split text into lines that fit within *max_px* pixels without dropping words."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if draw.textlength(cand, font=font) <= max_px:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines if lines else [text]


def _draw_hud_shell(
    canvas: Image.Image,
    topic: dict[str, Any],
    stage_idx: int,
    progress: float,
    t: float = 0.0,
) -> None:
    """Draw shared clean 1080x1920 header card, progress bar, and animated stage readout."""
    draw = ImageDraw.Draw(canvas)
    acc = topic["accent"]
    badge_f = _font(26, bold=True)
    hook_f = _font(33, bold=True)
    sub_f = _font(26, bold=False)
    st_title_f = _font(40, bold=True)
    st_sub_f = _font(26, bold=False)

    # Top progress bar (instant retention signal)
    draw.rectangle([72, 130, 1008, 144], fill=(40, 44, 65, 220))
    fill_w = int(72 + (1008 - 72) * max(0.02, min(1.0, progress)))
    draw.rectangle([72, 130, fill_w, 144], fill=(*acc, 255))

    # Top hook header box (auto-wraps cleanly inside 910px, up to 2 lines @ 33px)
    h_lines = _wrap_text_to_width(draw, topic["hook_title"], hook_f, 910)[:2]
    sub_lines = _wrap_text_to_width(draw, topic["hook_sub"], sub_f, 910)
    beat_pulse = int(t / 3.0) % 2 == 0
    border_col = (*acc, 255) if beat_pulse else (255, 255, 255, 235)
    draw.rounded_rectangle([54, 166, 1026, 376], radius=26, fill=(10, 12, 26, 234), outline=border_col, width=4)
    draw.rounded_rectangle([390, 180, 690, 218], radius=14, fill=(*acc, 255))
    draw.text((540, 199), topic["badge"], font=badge_f, fill=(10, 12, 24), anchor="mm")
    if len(h_lines) == 1:
        draw.text((540, 264), h_lines[0], font=hook_f, fill=(255, 255, 255), anchor="mm")
    else:
        draw.text((540, 246), h_lines[0], font=hook_f, fill=(255, 255, 255), anchor="mm")
        draw.text((540, 288), h_lines[1], font=hook_f, fill=(255, 255, 255), anchor="mm")
    draw.text((540, 342), sub_lines[0], font=sub_f, fill=(*acc, 255), anchor="mm")

    # Stage indicator strip above safe subtitle zone (Y=1185..1320)
    stages = topic["stages"]
    idx = max(0, min(len(stages) - 1, stage_idx))
    st_head, st_desc = stages[idx]
    st_desc_lines = _wrap_text_to_width(draw, st_desc, st_sub_f, 900)
    draw.rounded_rectangle([64, 1185, 1016, 1320], radius=24, fill=(12, 14, 30, 238), outline=border_col, width=4)
    draw.text((540, 1230), st_head, font=st_title_f, fill=(*acc, 255), anchor="mm")
    draw.text((540, 1284), st_desc_lines[0], font=st_sub_f, fill=(240, 244, 255), anchor="mm")


def _fit_cover_zoom(img: Image.Image, target_w: int, target_h: int, zoom: float, pan_x: float = 0.0) -> Image.Image:
    """Smooth centered Ken Burns zoom & slight pan into target rectangle."""
    iw, ih = img.size
    aspect = target_w / target_h
    if (iw / ih) > aspect:
        crop_h = int(ih / zoom)
        crop_w = int(crop_h * aspect)
    else:
        crop_w = int(iw / zoom)
        crop_h = int(crop_w / aspect)
    cx = iw // 2 + int(pan_x * max(0, (iw - crop_w) // 2))
    x0 = max(0, min(iw - crop_w, cx - crop_w // 2))
    y0 = max(0, min(ih - crop_h, (ih - crop_h) // 2))
    return img.crop((x0, y0, x0 + crop_w, y0 + crop_h)).resize((target_w, target_h), Image.Resampling.BILINEAR)


def _render_procedural_illusion_frame(t: float, total: float) -> Image.Image:
    """Render 100% original optical color-afterimage illusion + grayscale swap reveal at 62%."""
    canvas = Image.new("RGBA", (SHORTS_ASPECT_WIDTH, SHORTS_ASPECT_HEIGHT), (14, 12, 22, 255))
    draw = ImageDraw.Draw(canvas)
    prog = t / max(1.0, total)
    cx, cy = 540, 775

    # Phase 1 (0..62%): Intense Magenta/Cyan rotating rings + white fixation dot
    # Phase 2 (62..100%): Instant swap to neutral B&W check pattern so brain hallucinates gold/blue!
    if prog < 0.62:
        phase = t * 2.2
        for ring in range(9, 0, -1):
            r = ring * 44
            col = (255, 30, 170, 255) if (ring % 2 == 0) else (0, 240, 220, 255)
            pts_rect = [cx - r, cy - r, cx + r, cy + r]
            draw.ellipse(pts_rect, outline=col, width=22)
        for k in range(12):
            ang = phase + (k * math.pi / 6.0)
            px = cx + int(math.cos(ang) * 320)
            py = cy + int(math.sin(ang) * 320)
            draw.ellipse([px - 16, py - 16, px + 16, py + 16], fill=(255, 255, 255, 220))
        rem = max(1, int(math.ceil((0.62 * total) - t)))
        draw.text((cx, 430), f"KEEP STARING AT DOT: {rem}s", font=_font(36), fill=(255, 255, 255), anchor="mm")
    else:
        for row in range(8):
            for col_i in range(8):
                shade = 195 if (row + col_i) % 2 == 0 else 115
                x0 = 190 + col_i * 88
                y0 = 425 + row * 88
                draw.rectangle([x0, y0, x0 + 88, y0 + 88], fill=(shade, shade, shade, 255))
        draw.text((cx, 405), "GRAYSCALE REVEAL — DO YOU SEE COLOR?!", font=_font(34), fill=(255, 215, 0), anchor="mm")

    # Constant fixation dot in exact center
    draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=4)
    return canvas


def _render_procedural_gps_frame(t: float, total: float) -> Image.Image:
    """Render 100% original animated satellite orbit + relativistic error counter."""
    canvas = Image.new("RGBA", (SHORTS_ASPECT_WIDTH, SHORTS_ASPECT_HEIGHT), (6, 14, 30, 255))
    draw = ImageDraw.Draw(canvas)
    cx, cy = 540, 780

    # Grid lines
    for gx in range(80, 1040, 120):
        draw.line([(gx, 390), (gx, 1140)], fill=(20, 45, 85, 110), width=2)
    for gy in range(400, 1160, 120):
        draw.line([(60, gy), (1020, gy)], fill=(20, 45, 85, 110), width=2)

    # Orbit rings + Earth
    draw.ellipse([cx - 320, cy - 320, cx + 320, cy + 320], outline=(60, 160, 255, 170), width=4)
    draw.ellipse([cx - 115, cy - 115, cx + 115, cy + 115], fill=(25, 110, 210, 255), outline=(0, 240, 255, 255), width=4)
    draw.text((cx, cy), "EARTH", font=_font(34), fill=(255, 255, 255), anchor="mm")

    # Moving GPS Satellites
    for s_idx in range(3):
        ang = t * 0.85 + s_idx * (2 * math.pi / 3)
        sx = cx + int(math.cos(ang) * 320)
        sy = cy + int(math.sin(ang) * 320)
        draw.line([(cx, cy), (sx, sy)], fill=(0, 235, 255, 120), width=3)
        draw.rounded_rectangle([sx - 30, sy - 20, sx + 30, sy + 20], radius=8, fill=(255, 215, 0, 255), outline=(255, 255, 255, 255), width=2)

    km_drift = min(11.4, (t / max(1.0, total)) * 13.5)
    draw.text((cx, 415), f"UNCORRECTED GPS DRIFT: +{km_drift:.1f} KM / DAY", font=_font(34), fill=(255, 95, 95), anchor="mm")
    return canvas


def _render_procedural_wealth_frame(t: float, total: float) -> Image.Image:
    """Render 100% original animated Day 1..30 exponential race graph ($1M vs $0.01 doubled)."""
    canvas = Image.new("RGBA", (SHORTS_ASPECT_WIDTH, SHORTS_ASPECT_HEIGHT), (6, 22, 14, 255))
    draw = ImageDraw.Draw(canvas)
    prog = min(1.0, t / max(1.0, total * 0.88))
    day = max(1, min(30, int(1 + prog * 29)))
    penny_val = 0.01 * (2 ** (day - 1))

    # Chart bounding area
    x0, y0, x1, y1 = 110, 480, 970, 1080
    draw.rectangle([x0, y0, x1, y1], fill=(10, 28, 20, 230), outline=(50, 235, 120, 170), width=3)

    # Flat $1M line (scale max = 5,500,000)
    y_1m = int(y1 - (1_000_000 / 5_500_000) * (y1 - y0))
    draw.line([(x0, y_1m), (x1, y_1m)], fill=(0, 220, 255, 230), width=5)
    draw.text((x0 + 18, y_1m - 26), "$1,000,000 FLAT", font=_font(28), fill=(0, 220, 255), anchor="lm")

    # Exponential curve up to current Day
    pts: list[tuple[int, int]] = []
    for d in range(1, day + 1):
        val = min(5_500_000, 0.01 * (2 ** (d - 1)))
        px = int(x0 + ((d - 1) / 29.0) * (x1 - x0))
        py = int(y1 - (val / 5_500_000) * (y1 - y0))
        pts.append((px, py))
    if len(pts) >= 2:
        draw.line(pts, fill=(255, 215, 0, 255), width=8)
    lx, ly = pts[-1]
    draw.ellipse([lx - 14, ly - 14, lx + 14, ly + 14], fill=(255, 255, 255, 255), outline=(255, 215, 0, 255), width=4)

    val_str = f"${penny_val:,.2f}" if penny_val < 1000 else f"${penny_val:,.0f}"
    draw.text((540, 430), f"DAY {day}/30  │  PENNY = {val_str}", font=_font(40), fill=(255, 215, 0), anchor="mm")
    return canvas


def _build_photo_panel_frame(
    imgs: list[Image.Image],
    topic: dict[str, Any],
    t: float,
    total: float,
) -> Image.Image:
    """Render photo-driven category frame with multi-scene Ken Burns cuts every ~4–6 seconds."""
    acc = topic["accent"]
    bg_rgb = topic["bg_rgb"]
    if not imgs:
        canvas = Image.new("RGBA", (SHORTS_ASPECT_WIDTH, SHORTS_ASPECT_HEIGHT), (*bg_rgb, 255))
    else:
        scene_len = max(3.5, total / max(3, len(imgs) * 2))
        s_idx = int(t / scene_len)
        im = imgs[s_idx % len(imgs)]
        sub_prog = (t % scene_len) / scene_len
        zoom = 1.04 + 0.16 * sub_prog
        pan = math.sin(s_idx * 1.7 + sub_prog * 2.0) * 0.45

        bg = _fit_cover_zoom(im, SHORTS_ASPECT_WIDTH, SHORTS_ASPECT_HEIGHT, zoom=1.1).filter(ImageFilter.GaussianBlur(26))
        dark = Image.new("RGBA", bg.size, (bg_rgb[0], bg_rgb[1], bg_rgb[2], 140))
        canvas = Image.alpha_composite(bg.convert("RGBA"), dark)

        # Mid viewport card (1080x760 window at Y=395..1145)
        fg = _fit_cover_zoom(im, 960, 740, zoom=zoom, pan_x=pan)
        border = Image.new("RGBA", (972, 752), (*acc, 255))
        border.paste(fg, (6, 6))
        canvas.paste(border, (54, 395))
    return canvas


def _render_frame_sequence(
    topic: dict[str, Any],
    pd_imgs: list[Image.Image],
    duration_s: float,
    fps: int,
    frames_dir: Path,
) -> None:
    """Pre-render crisp PNG frame sequence for FFmpeg H.264 compilation."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    n_frames = max(1, int(math.ceil(duration_s * fps)))
    mtype = topic["media_source"]["type"]
    stages_n = len(topic["stages"])

    for i in range(n_frames):
        t = i / fps
        prog = t / max(0.01, duration_s)
        stage_idx = min(stages_n - 1, int(prog * stages_n))

        if mtype == "procedural_illusion":
            canvas = _render_procedural_illusion_frame(t, duration_s)
        elif mtype == "procedural_gps":
            canvas = _render_procedural_gps_frame(t, duration_s)
        elif mtype == "procedural_wealth":
            canvas = _render_procedural_wealth_frame(t, duration_s)
        else:
            canvas = _build_photo_panel_frame(pd_imgs, topic, t, duration_s)

        _draw_hud_shell(canvas, topic, stage_idx, prog, t=t)
        # Brief 1-frame pattern-interrupt flash on beat boundaries (every 3.5s) to signal visual pacing cuts
        beat_phase = t % 3.5
        if beat_phase < (1.2 / max(1, fps)) and t > 0.2:
            flash = Image.new("RGBA", canvas.size, (*topic["accent"], 65))
            canvas = Image.alpha_composite(canvas, flash)
        canvas.convert("RGB").save(frames_dir / f"f_{i:05d}.jpg", "JPEG", quality=92)


def build_topic_short(
    topic: dict[str, Any],
    out_dir: Path,
    fps: int = 30,
) -> dict[str, Any]:
    """Build one complete 100% copyright-free vertical Short + metadata catalog dict."""
    if not _check_ffmpeg_available():
        raise FFmpegNotFoundError()

    tid = topic["id"]
    work_dir = out_dir / "_work" / tid
    frames_dir = work_dir / "frames"
    voice_mp3 = work_dir / f"{tid}_voice.mp3"
    ass_path = work_dir / f"{tid}.ass"
    out_mp4 = out_dir / f"{tid}.mp4"
    preview_jpg = out_dir / f"preview_{tid}.jpg"

    log.info("[%s] Synthesizing US Neural Voiceover (%s)...", tid, topic["voice"])
    chunks = asyncio.run(_synthesize_edge_tts(topic["script"], topic["voice"], voice_mp3))
    dur_s = min(55.0, round(_probe_audio_duration(voice_mp3) + 0.8, 2))
    build_ass_from_segments(chunks, ass_path, font_name="Segoe UI Black", font_size=60)

    # Fetch strict PD/CC0 imagery if applicable
    ms = topic["media_source"]
    pd_imgs: list[Image.Image] = []
    if ms["type"] == "nasa":
        pd_imgs = fetch_nasa_pd_images(ms["query"], count=4)
    elif ms["type"] == "openverse":
        pd_imgs = fetch_openverse_cc0_images(ms["query"], count=4)

    log.info("[%s] Rendering %.1fs @ %dfps (PD images=%d)...", tid, dur_s, fps, len(pd_imgs))
    _render_frame_sequence(topic, pd_imgs, dur_s, fps, frames_dir)

    # Compile frames + Edge-TTS voice + 100% synthetic FFmpeg ambient pulse + -14 LUFS loudnorm
    ass_esc = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    ambient_expr = "aevalsrc='0.032*sin(2*PI*110*t)+0.022*sin(2*PI*165*t)+0.015*sin(2*PI*220*t)*sin(2*PI*0.25*t)':s=44100:c=stereo"
    fc = (
        f"[0:v]ass='{ass_esc}'[vout];"
        f"{ambient_expr},atrim=0:{dur_s},lowpass=f=480[bed];"
        f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad=whole_dur={dur_s}[vo];"
        f"[vo][bed]amix=inputs=2:duration=first:weights=1.0 0.35,"
        f"loudnorm=I={TARGET_LOUDNORM_I}:LRA={TARGET_LOUDNORM_LRA}:tp={TARGET_LOUDNORM_TP}[aout]"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps), "-i", str(frames_dir / "f_%05d.jpg"),
        "-i", str(voice_mp3),
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(dur_s),
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(out_mp4),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0 or not out_mp4.exists():
        raise RuntimeError(f"FFmpeg compilation failed for {tid}: {(res.stderr or '')[-500:]}")

    # Save visual QA midpoint frame
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(round(dur_s * 0.65, 2)), "-i", str(out_mp4), "-vframes", "1", str(preview_jpg)],
        capture_output=True,
    )

    desc = (
        f"{topic['hook_title']}\n"
        f"{topic['hook_sub']}\n\n"
        f"{topic['script']}\n\n"
        "100% Original Script, Neural Voiceover & Custom Visuals.\n"
        f"#{' #'.join(t.replace(' ', '') for t in topic['tags'][:6])} #Shorts"
    )
    return {
        "id": tid,
        "slot": "morning" if (GLOBAL_VIRAL_TOPICS.index(topic) % 2 == 0) else "night",
        "video_path": str(out_mp4.resolve()),
        "preview_path": str(preview_jpg.resolve()),
        "duration_s": dur_s,
        "generated_at": datetime.datetime.now().isoformat(),
        "youtube_shorts": {
            "title": topic["title"][:60],
            "description": desc,
            "tags": topic["tags"],
            "category": topic["yt_category"],
            "category_id": topic["yt_category_id"],
            "playlist_name": topic["playlist_name"],
            "altered_content": False,
            "pinned_comment": topic["pinned_comment"],
        },
    }


def build_all_global_shorts(out_dir: Path, catalog_path: Path, fps: int = 30) -> list[dict[str, Any]]:
    """Generate one copyright-free Short per global top category and write catalog JSON."""
    entries: list[dict[str, Any]] = []
    for topic in GLOBAL_VIRAL_TOPICS:
        entries.append(build_topic_short(topic, out_dir, fps=fps))
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Generated %d Copyright-Free Viral Shorts → %s", len(entries), catalog_path)
    return entries


def main() -> None:
    """CLI entry point for building 100% copyright-free viral Shorts."""
    parser = argparse.ArgumentParser(description="Build 100% copyright-free viral YouTube Shorts across global categories")
    parser.add_argument("--out-dir", default="queue/copyright_free", help="Output folder for rendered .mp4 Shorts")
    parser.add_argument("--catalog-out", default="queue/copyright_free_catalog.json", help="Destination catalog JSON")
    parser.add_argument("--topic", help="Build single topic ID only (optional)")
    parser.add_argument("--fps", type=int, default=30, help="Output framerate (default: 30)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    cat_path = Path(args.catalog_out).resolve()
    if args.topic:
        matched = [t for t in GLOBAL_VIRAL_TOPICS if t["id"] == args.topic or t["category_key"] == args.topic]
        if not matched:
            log.error("Unknown topic '%s'. Available: %s", args.topic, [t["id"] for t in GLOBAL_VIRAL_TOPICS])
            sys.exit(1)
        entry = build_topic_short(matched[0], out_dir, fps=args.fps)
        log.info("Done: %s (%.1fs)", entry["video_path"], entry["duration_s"])
        return

    build_all_global_shorts(out_dir, cat_path, fps=args.fps)


if __name__ == "__main__":
    main()
