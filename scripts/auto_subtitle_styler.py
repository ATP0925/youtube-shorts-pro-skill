"""
Viral Kinetic ASS Subtitle Generator & FFmpeg Short Remastering Tool.

Implements the editing-tools-automation specification:
  1. Converts Whisper word/segment JSON or phrase transcripts into 1080×1920
     ASS subtitles positioned cleanly in the dual YouTube/IG UI safe zone
     (``MarginV=520``, away from right-side icons & bottom descriptions).
  2. Applies kinetic pop-in scale animations and rotating high-contrast
     keyword highlight styles (Yellow, Cyan, Green, Red).
  3. Renders vertical 9:16 clips with blurred landscape background padding,
     EBU R128 broadcast loudness normalization (``-14 LUFS``), and burned ASS.
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
    SHORTS_ASPECT_HEIGHT,
    SHORTS_ASPECT_WIDTH,
    TARGET_LOUDNORM_I,
    TARGET_LOUDNORM_LRA,
    TARGET_LOUDNORM_TP,
    VIRAL_SAFE_MARGIN_V,
)
from exceptions import FFmpegNotFoundError
from logger import get_logger
from media_loudness_validator import _check_ffmpeg_available

log = get_logger(__name__)

__all__ = ["format_ass_timestamp", "build_ass_from_segments", "whisper_json_to_segments", "render_viral_short"]

DEFAULT_STYLE_CYCLE = ("ViralYellow", "ViralCyan", "ViralGreen", "ViralRed")


def format_ass_timestamp(seconds: float) -> str:
    """Convert seconds into ASS ``H:MM:SS.cs`` format."""
    secs = max(0.0, float(seconds))
    hrs = int(secs // 3600)
    mins = int((secs % 3600) // 60)
    rem = secs % 60.0
    return f"{hrs}:{mins:02d}:{rem:05.2f}"


def whisper_json_to_segments(whisper_data: dict[str, Any], max_words_per_chunk: int = 4) -> list[dict[str, Any]]:
    """Chunk OpenAI Whisper JSON word/segment output into 1–4 word viral subtitle beats."""
    segments: list[dict[str, Any]] = []
    words_pool: list[dict[str, Any]] = []
    for seg in whisper_data.get("segments", []):
        if seg.get("words"):
            words_pool.extend(seg["words"])
        elif seg.get("text"):
            segments.append({
                "start": float(seg.get("start", 0.0)),
                "end": float(seg.get("end", 0.0)),
                "text": seg["text"].strip().upper(),
            })

    if words_pool:
        for i in range(0, len(words_pool), max_words_per_chunk):
            chunk = words_pool[i:i + max_words_per_chunk]
            text = " ".join(str(w.get("word", "")).strip() for w in chunk).strip().upper()
            if text:
                segments.append({
                    "start": float(chunk[0].get("start", 0.0)),
                    "end": float(chunk[-1].get("end", 0.0)),
                    "text": text,
                })
    return segments


def build_ass_from_segments(
    segments: list[dict[str, Any]],
    out_ass_path: str | Path,
    font_name: str = "Montserrat",
    font_size: int = 62,
    margin_v: int = VIRAL_SAFE_MARGIN_V,
) -> Path:
    """Write a kinetic pop-in 1080×1920 ASS subtitle file from timed text segments."""
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {SHORTS_ASPECT_WIDTH}\n"
        f"PlayResY: {SHORTS_ASPECT_HEIGHT}\n"
        "WrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: ViralYellow,{font_name},{font_size},&H0000FFFF,&H000000FF,&H00000000,&HB0000000,"
        f"-1,0,0,0,100,100,1,0,1,6,3,2,60,120,{margin_v},1\n"
        f"Style: ViralCyan,{font_name},{font_size},&H00FFFF00,&H000000FF,&H00000000,&HB0000000,"
        f"-1,0,0,0,100,100,1,0,1,6,3,2,60,120,{margin_v},1\n"
        f"Style: ViralGreen,{font_name},{font_size},&H0032CD32,&H000000FF,&H00000000,&HB0000000,"
        f"-1,0,0,0,100,100,1,0,1,6,3,2,60,120,{margin_v},1\n"
        f"Style: ViralRed,{font_name},{font_size + 2},&H003030FF,&H000000FF,&H00000000,&HB0000000,"
        f"-1,0,0,0,102,102,1,0,1,6,4,2,60,120,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines: list[str] = []
    for idx, seg in enumerate(segments):
        st = format_ass_timestamp(seg["start"])
        en = format_ass_timestamp(seg["end"])
        style = seg.get("style") or DEFAULT_STYLE_CYCLE[idx % len(DEFAULT_STYLE_CYCLE)]
        txt = str(seg.get("text", "")).replace("\n", "\\N")
        if txt:
            lines.append(
                f"Dialogue: 0,{st},{en},{style},,0,0,0,,"
                f"{{\\t(0,60,\\fscx114\\fscy114)\\t(60,120,\\fscx100\\fscy100)}}{txt}"
            )

    dest = Path(out_ass_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    log.info("Generated ASS subtitles (%d lines) → %s", len(lines), dest)
    return dest


def render_viral_short(
    input_video: str,
    output_video: str,
    ass_path: str | Path | None = None,
    trim_start: float | None = None,
    trim_end: float | None = None,
    blur_vertical: bool = True,
    normalize_audio: bool = True,
) -> bool:
    """Render a vertical 1080×1920 viral Short with optional blurred padding, ASS burn, and -14 LUFS loudness."""
    if not _check_ffmpeg_available():
        raise FFmpegNotFoundError()
    if not os.path.exists(input_video):
        log.error("Input video not found: %s", input_video)
        return False

    chains: list[str] = []
    cur_label = "0:v"
    if blur_vertical:
        chains.append(
            f"[{cur_label}]scale={SHORTS_ASPECT_WIDTH}:{SHORTS_ASPECT_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={SHORTS_ASPECT_WIDTH}:{SHORTS_ASPECT_HEIGHT},boxblur=28:5[bg]"
        )
        chains.append(f"[{cur_label}]scale={SHORTS_ASPECT_WIDTH}:-2[fg]")
        chains.append("[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase]")
        cur_label = "vbase"
    if ass_path:
        ass_esc = str(Path(ass_path).resolve()).replace("\\", "/").replace(":", "\\:")
        chains.append(f"[{cur_label}]ass='{ass_esc}'[vout]")
        cur_label = "vout"
    elif cur_label == "0:v":
        chains.append("[0:v]null[vout]")
        cur_label = "vout"

    cmd: list[str] = ["ffmpeg", "-y"]
    if trim_start is not None:
        cmd.extend(["-ss", str(trim_start)])
    if trim_end is not None:
        cmd.extend(["-to", str(trim_end)])
    cmd.extend(["-i", input_video, "-filter_complex", ";".join(chains), "-map", f"[{cur_label}]", "-map", "0:a?"])
    if normalize_audio:
        cmd.extend(["-af", f"loudnorm=I={TARGET_LOUDNORM_I}:LRA={TARGET_LOUDNORM_LRA}:tp={TARGET_LOUDNORM_TP}"])
    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_video,
    ])

    Path(output_video).parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0 or not os.path.exists(output_video):
        log.error("FFmpeg render failed: %s", (res.stderr or "")[-500:])
        return False
    log.info("Rendered viral Short → %s", output_video)
    return True


def main() -> None:
    """Standalone CLI for generating kinetic ASS subtitles and rendering viral Shorts."""
    parser = argparse.ArgumentParser(description="Kinetic ASS Subtitle Generator & Viral Short Renderer")
    parser.add_argument("--whisper-json", help="Path to Whisper JSON transcript (with timestamps)")
    parser.add_argument("--out-ass", help="Output .ass file path")
    parser.add_argument("--render-input", help="Optional input video to remaster")
    parser.add_argument("--render-output", help="Optional output 1080x1920 .mp4 path")
    parser.add_argument("--no-blur-vertical", action="store_true", help="Skip 9:16 blur-fill (already vertical)")
    parser.add_argument("--no-loudnorm", action="store_true", help="Skip -14 LUFS loudness normalization")
    args = parser.parse_args()

    ass_dest: Path | None = Path(args.out_ass) if args.out_ass else None
    if args.whisper_json:
        wdata = json.loads(Path(args.whisper_json).read_text(encoding="utf-8"))
        segs = whisper_json_to_segments(wdata)
        ass_dest = ass_dest or Path(args.whisper_json).with_suffix(".ass")
        build_ass_from_segments(segs, ass_dest)

    if args.render_input and args.render_output:
        ok = render_viral_short(
            args.render_input,
            args.render_output,
            ass_path=ass_dest,
            blur_vertical=not args.no_blur_vertical,
            normalize_audio=not args.no_loudnorm,
        )
        sys.exit(0 if ok else 1)

    if not args.whisper_json and not args.render_input:
        parser.print_help()


if __name__ == "__main__":
    main()
