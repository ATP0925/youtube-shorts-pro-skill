"""
Master YouTube Shorts Pro Daily Operations Pipeline.

CLI orchestrator:
  --verify         Validate all queued Shorts (9:16, <60s, loudness, metadata)
  --audit          Scrape Studio Analytics, Feature Eligibility, Home Tab & Comments Inbox
  --optimize-live  Enable Home Tab, Subscribe Watermark, COPPA default & backfill live Shorts
  --slot morning|night|auto [--daily-ops] [--scheduled] [--dry-run] [--count N]
  --status         Print current channel & upload history summary
  --verbose        Enable debug-level logging
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import acquire_process_lock, load_config, load_json, save_json, validate_config
from constants import DEFAULT_MORNING_WINDOW, DEFAULT_NIGHT_START_HOUR, NIGHT_WINDOW_MINUTE_THRESHOLD
from exceptions import YTProError
from logger import get_logger
from media_loudness_validator import check_audio_loudness, probe_video, verify_catalog_items
from yt_channel_manager import (
    audit_and_collect_analytics,
    backfill_live_shorts,
    configure_pro_studio_foundation,
    load_channel_state,
    save_channel_state,
)
from yt_studio_shorts_uploader import check_youtube_session_health, upload_youtube_short

log = get_logger(__name__)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

__all__ = ["run_yt_slot", "main"]


def _select_next_short(slot: str, history: dict[str, Any], catalog: list[dict]) -> dict | None:
    """Pick the next unuploaded Short for the given slot."""
    uploaded = {u["id"] for u in history.get("uploads", []) if u.get("status") == "SUCCESS"}
    preferred = [
        e for e in catalog
        if e.get("slot") == slot and e["id"] not in uploaded and os.path.exists(e.get("video_path", ""))
    ]
    if preferred:
        return preferred[0]
    fallback = [e for e in catalog if e["id"] not in uploaded and os.path.exists(e.get("video_path", ""))]
    return fallback[0] if fallback else None


def _is_same_date(iso_ts: str | None, target_date: datetime.date) -> bool:
    """Check if an ISO timestamp falls on the given date."""
    if not iso_ts:
        return False
    try:
        return datetime.datetime.fromisoformat(iso_ts).date() == target_date
    except Exception:
        return False


def _within_scheduled_window(slot: str, now: datetime.datetime, cfg: dict[str, Any]) -> bool:
    """Check if the current time falls within the allowed slot window."""
    start_h, end_h = cfg.get("morning_window_hours", list(DEFAULT_MORNING_WINDOW))
    night_h = cfg.get("night_window_start_hour", DEFAULT_NIGHT_START_HOUR)
    if slot == "morning":
        return start_h <= now.hour < end_h or (now.hour == end_h and now.minute < NIGHT_WINDOW_MINUTE_THRESHOLD)
    return (now.hour == night_h and now.minute >= NIGHT_WINDOW_MINUTE_THRESHOLD) or now.hour > night_h


def run_yt_slot(
    slot: str,
    dry_run: bool = False,
    count: int = 1,
    scheduled: bool = False,
    daily_ops: bool = False,
) -> bool:
    """Execute the daily upload pipeline for the given slot.

    Args:
        slot: "morning" or "night".
        dry_run: Validate without uploading.
        count: Number of Shorts to upload.
        scheduled: Whether triggered by Task Scheduler.
        daily_ops: Whether to run analytics + comments before upload.

    Returns:
        ``True`` if all uploads succeeded.
    """
    cfg = load_config()
    now_dt = datetime.datetime.now()

    log.info("╔" + "═" * 70 + "╗")
    log.info("║  YOUTUBE SHORTS PRO PIPELINE — [%s SLOT]", slot.upper())
    log.info("║  Time: %s │ Dry-Run: %s │ Mode: %s",
             now_dt.strftime("%Y-%m-%d %H:%M:%S"), dry_run, "SCHEDULED" if scheduled else "MANUAL")
    log.info("╚" + "═" * 70 + "╝")

    if scheduled and not _within_scheduled_window(slot, now_dt, cfg):
        log.info("Skipped stale scheduled %s trigger at %s (outside window).", slot, now_dt.strftime("%H:%M"))
        return False

    history = load_json(cfg["history_path"], {"last_morning": None, "last_night": None, "uploads": []})
    if scheduled and _is_same_date(history.get(f"last_{slot}"), now_dt.date()):
        log.info("Scheduled %s slot already succeeded today (%s). Skipping.", slot, now_dt.date())
        return False

    health = asyncio.run(check_youtube_session_health())
    log.info("[SESSION] %s", health.get("message", ""))
    if not health.get("healthy") and not dry_run:
        return False

    st = load_channel_state()
    ch_id = st.get("channel_id") or health.get("channel_id")
    if ch_id and not st.get("channel_id"):
        st["channel_id"] = ch_id
        save_channel_state(st)

    if (daily_ops or scheduled) and not dry_run:
        rep = asyncio.run(audit_and_collect_analytics(reply_comments=True, channel_id_override=ch_id))
        log.info("[ANALYTICS] subs=%s views_28d=%s home_tab=%s comments_replied=%d",
                 rep.get("dashboard_summary", {}).get("subscribers"),
                 rep.get("dashboard_summary", {}).get("views_28d"),
                 rep.get("home_tab_enabled"),
                 len(rep.get("unresponded_comments_handled", [])))

    catalog = load_json(cfg["catalog_path"], [])

    for i in range(count):
        item = _select_next_short(slot, history, catalog)
        if not item:
            log.info("All queued Shorts have been uploaded.")
            break
        yt = item["youtube_shorts"]
        pr = probe_video(item["video_path"])
        ld = check_audio_loudness(item["video_path"])
        log.info("[SELECTED %d/%d] %s │ %s │ %.1fs │ mean=%s dB │ playlist=%s",
                 i + 1, count, item["id"], yt["title"],
                 pr.get("duration", 0), ld.get("mean_db"), yt.get("playlist_name"))

        if pr.get("error") or not (pr.get("is_9_16") and pr.get("under_60s")) or not ld.get("ok"):
            log.error("Selected media failed validation guard.")
            return False
        if dry_run:
            log.info("[DRY-RUN] Verified video, loudness, metadata & CTA comment.")
            continue

        res = asyncio.run(
            upload_youtube_short(
                video_path=item["video_path"],
                title=yt["title"],
                description=yt["description"],
                tags=yt.get("tags", []),
                channel_id=ch_id,
                visibility="Public",
                playlist_name=yt.get("playlist_name"),
                game_title=yt.get("game_title", cfg.get("default_game_title")),
                altered_content=bool(yt.get("altered_content", False)),
                pinned_comment=yt.get("pinned_comment"),
            )
        )
        log.info("[UPLOAD] %s — %s", "SUCCESS" if res.get("success") else "FAILED", res.get("message", ""))
        if res.get("success"):
            done_dt = datetime.datetime.now()
            history[f"last_{slot}"] = done_dt.isoformat()
            history["uploads"].append({
                "id": item["id"],
                "slot": slot,
                "title": yt["title"],
                "video_id": res.get("video_id"),
                "video_url": res.get("video_url"),
                "datetime": done_dt.isoformat(),
                "status": "SUCCESS",
            })
            save_json(cfg["history_path"], history)
        else:
            return False
    return True


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="YouTube Shorts Pro Skill Pipeline")
    parser.add_argument("--slot", choices=["morning", "night", "auto"], default="auto")
    parser.add_argument("--verify", action="store_true", help="Validate all catalog entries")
    parser.add_argument("--dry-run", action="store_true", help="Validate without uploading")
    parser.add_argument("--scheduled", action="store_true", help="Triggered by Task Scheduler")
    parser.add_argument("--daily-ops", action="store_true", help="Run analytics + comments first")
    parser.add_argument("--audit", action="store_true", help="Run audit only")
    parser.add_argument("--optimize-live", action="store_true", help="Setup Studio foundation")
    parser.add_argument("--count", type=int, default=1, help="Number of Shorts to upload")
    parser.add_argument("--status", action="store_true", help="Print channel status")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.getLogger("yt_pro").setLevel(logging.DEBUG)

    try:
        cfg = validate_config(load_config(), require_channel_id=False)

        if args.verify:
            catalog = load_json(cfg["catalog_path"], [])
            sys.exit(0 if verify_catalog_items(catalog, check_loudness=True, raise_on_missing_ffmpeg=True) else 1)

        if args.status:
            h = load_json(cfg["history_path"], {"uploads": []})
            st = load_channel_state()
            log.info("Channel: %s (%s)", st.get("channel_name", "?"), st.get("channel_id", "?"))
            log.info("Last Morning: %s │ Last Night: %s", h.get("last_morning"), h.get("last_night"))
            log.info("Total Uploads: %d", len(h.get("uploads", [])))
            return

        with acquire_process_lock() as ok_lock:
            if not ok_lock:
                log.warning("Another pipeline instance is active. Exiting.")
                return
            if args.optimize_live:
                log.info("[FOUNDATION] %s", asyncio.run(configure_pro_studio_foundation()))
                catalog = load_json(cfg["catalog_path"], [])
                hist = load_json(cfg["history_path"], {"uploads": []})
                log.info("[BACKFILL] %s", json.dumps(asyncio.run(backfill_live_shorts(catalog, hist)), indent=2))
                log.info("[AUDIT] %s", json.dumps(asyncio.run(audit_and_collect_analytics()), indent=2))
                return
            if args.audit:
                log.info(json.dumps(asyncio.run(audit_and_collect_analytics()), indent=2))
                return

            slot = args.slot
            if slot == "auto":
                now_t = datetime.datetime.now()
                night_h = cfg.get("night_window_start_hour", DEFAULT_NIGHT_START_HOUR)
                is_morning = now_t.hour < night_h or (
                    now_t.hour == night_h and now_t.minute < NIGHT_WINDOW_MINUTE_THRESHOLD
                )
                slot = "morning" if is_morning else "night"

            ok = run_yt_slot(
                slot,
                dry_run=args.dry_run,
                count=args.count,
                scheduled=args.scheduled,
                daily_ops=args.daily_ops,
            )
            sys.exit(0 if ok else 1)

    except YTProError as exc:
        log.error("Pipeline halted cleanly: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        log.warning("Pipeline interrupted by user (Ctrl+C). Exiting gracefully.")
        sys.exit(130)


if __name__ == "__main__":
    main()
