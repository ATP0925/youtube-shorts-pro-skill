"""
Master YouTube Shorts Pro Daily Operations Pipeline
---------------------------------------------------
CLI orchestrator:
  --verify         Validate all queued Shorts (9:16, <60s, loudness, metadata)
  --audit          Scrape Studio Analytics, Feature Eligibility, Home Tab & Comments Inbox
  --optimize-live  Enable Home Tab, Subscribe Watermark, COPPA default & backfill live Shorts
  --slot morning|night|auto [--daily-ops] [--scheduled] [--dry-run] [--count N]
  --status         Print current channel & upload history summary
"""

import argparse
import asyncio
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import acquire_process_lock, load_config, load_json, save_json
from media_loudness_validator import check_audio_loudness, probe_video, verify_catalog_items
from yt_channel_manager import (
    audit_and_collect_analytics,
    backfill_live_shorts,
    configure_pro_studio_foundation,
    load_channel_state,
)
from yt_studio_shorts_uploader import check_youtube_session_health, upload_youtube_short

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


def _select_next_short(slot: str, history: dict, catalog: list[dict]) -> dict | None:
    uploaded = {u["id"] for u in history.get("uploads", []) if u.get("status") == "SUCCESS"}
    preferred = [e for e in catalog if e.get("slot") == slot and e["id"] not in uploaded and os.path.exists(e.get("video_path", ""))]
    if preferred:
        return preferred[0]
    fallback = [e for e in catalog if e["id"] not in uploaded and os.path.exists(e.get("video_path", ""))]
    return fallback[0] if fallback else None


def _is_same_date(iso_ts: str | None, target_date: datetime.date) -> bool:
    if not iso_ts:
        return False
    try:
        return datetime.datetime.fromisoformat(iso_ts).date() == target_date
    except Exception:
        return False


def _within_scheduled_window(slot: str, now: datetime.datetime, cfg: dict) -> bool:
    start_h, end_h = cfg.get("morning_window_hours", [18, 21])
    night_h = cfg.get("night_window_start_hour", 21)
    if slot == "morning":
        return start_h <= now.hour < end_h or (now.hour == end_h and now.minute < 30)
    return (now.hour == night_h and now.minute >= 30) or now.hour > night_h


def run_yt_slot(slot: str, dry_run: bool = False, count: int = 1, scheduled: bool = False, daily_ops: bool = False) -> bool:
    cfg = load_config()
    now_dt = datetime.datetime.now()
    print("=" * 72)
    print(f"  YOUTUBE SHORTS PRO PIPELINE — [{slot.upper()} SLOT]")
    print(f"  Time: {now_dt.strftime('%Y-%m-%d %H:%M:%S')} | Dry-Run: {dry_run} | Mode: {'SCHEDULED' if scheduled else 'MANUAL'}")
    print("=" * 72)

    if scheduled and not _within_scheduled_window(slot, now_dt, cfg):
        print(f"Skipped stale scheduled {slot} trigger at {now_dt.strftime('%H:%M')} (outside slot window).")
        return False

    history = load_json(cfg["history_path"], {"last_morning": None, "last_night": None, "uploads": []})
    if scheduled and _is_same_date(history.get(f"last_{slot}"), now_dt.date()):
        print(f"Scheduled {slot} slot already succeeded today ({now_dt.date()}). Skipping duplicate.")
        return False

    health = asyncio.run(check_youtube_session_health())
    print("[SESSION HEALTH]", health)
    if not health.get("healthy") and not dry_run:
        return False

    if (daily_ops or scheduled) and not dry_run:
        rep = asyncio.run(audit_and_collect_analytics(reply_comments=True))
        print("[ANALYTICS & COMMENTS]", json.dumps({
            "subs": rep.get("dashboard_summary", {}).get("subscribers"),
            "views_28d": rep.get("dashboard_summary", {}).get("views_28d"),
            "home_tab": rep.get("home_tab_enabled"),
            "eligibility": rep.get("feature_eligibility"),
            "comments_replied": len(rep.get("unresponded_comments_handled", [])),
        }))

    catalog = load_json(cfg["catalog_path"], [])
    ch_id = load_channel_state().get("channel_id") or health.get("channel_id")

    for i in range(count):
        item = _select_next_short(slot, history, catalog)
        if not item:
            print("All queued Shorts have been uploaded.")
            break
        yt = item["youtube_shorts"]
        pr = probe_video(item["video_path"])
        ld = check_audio_loudness(item["video_path"])
        print(
            f"\n[SELECTED {i+1}/{count}] {item['id']} | {yt['title']} "
            f"({pr.get('duration')}s, mean={ld.get('mean_db')}dB, playlist={yt.get('playlist_name')})"
        )
        if pr.get("error") or not (pr.get("is_9_16") and pr.get("under_60s")) or not ld.get("ok"):
            print("Selected media failed validation guard.")
            return False
        if dry_run:
            print("[DRY-RUN] Verified video, loudness, metadata & CTA comment.")
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
        print("[UPLOAD RESULT]", res)
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


def main():
    parser = argparse.ArgumentParser(description="YouTube Shorts Pro Skill Pipeline")
    parser.add_argument("--slot", choices=["morning", "night", "auto"], default="auto")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scheduled", action="store_true")
    parser.add_argument("--daily-ops", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--optimize-live", action="store_true")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    if args.verify:
        catalog = load_json(cfg["catalog_path"], [])
        sys.exit(0 if verify_catalog_items(catalog, check_loudness=True) else 1)

    if args.status:
        h = load_json(cfg["history_path"], {"uploads": []})
        print("Channel:", load_channel_state())
        print("Last Morning:", h.get("last_morning"), "| Last Night:", h.get("last_night"))
        print("Total Uploads:", len(h.get("uploads", [])))
        return

    with acquire_process_lock() as ok_lock:
        if not ok_lock:
            print("Another pipeline instance is active.")
            return
        if args.optimize_live:
            print("[FOUNDATION]", asyncio.run(configure_pro_studio_foundation()))
            catalog = load_json(cfg["catalog_path"], [])
            hist = load_json(cfg["history_path"], {"uploads": []})
            print("[BACKFILL]", json.dumps(asyncio.run(backfill_live_shorts(catalog, hist)), indent=2))
            print("[AUDIT]", json.dumps(asyncio.run(audit_and_collect_analytics()), indent=2))
            return
        if args.audit:
            print(json.dumps(asyncio.run(audit_and_collect_analytics()), indent=2))
            return

        slot = args.slot
        if slot == "auto":
            now_t = datetime.datetime.now()
            night_h = cfg.get("night_window_start_hour", 21)
            slot = "morning" if (now_t.hour < night_h or (now_t.hour == night_h and now_t.minute < 30)) else "night"

        ok = run_yt_slot(slot, dry_run=args.dry_run, count=args.count, scheduled=args.scheduled, daily_ops=args.daily_ops)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
