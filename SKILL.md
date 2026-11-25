---
name: youtube-shorts-pro-skill
description: >-
  Use when setting up, optimizing, auditing, or automating a YouTube Shorts
  or high-RPM US-audience gaming channel — including Studio CDP uploads,
  branding assets, media validation, analytics scraping, comment management,
  EST/PST scheduling, and optional Instagram Reels cross-posting.
metadata:
  category: automation
  triggers:
    - youtube shorts
    - youtube studio automation
    - gaming channel setup
    - high rpm monetization
    - adsense ypp
    - cdp playwright upload
    - instagram reels
    - shorts metadata
    - channel branding
    - upload pipeline
  author: ATP0925
  version: "1.1.0"
---

# YouTube Shorts Pro Skill (`youtube-shorts-pro-skill`)

Complete AI-agent operating system for building, upgrading, auditing, and running a monetizable YouTube Shorts channel (especially targeting Tier-1 USA/English RPM) alongside an optional Instagram Reels dual-slot pipeline.

## When to Use

- Building or rebranding a YouTube / Shorts channel to look and perform like a top creator
- Optimizing a channel toward USA / UK / CA / AU high-RPM English viewers while preserving local AdSense payouts (e.g. India PAN + Form `W-8BEN`)
- Automating YouTube Studio uploads via Chrome CDP with **complete pro metadata** (Playlists, Category `Gaming`, official `Game title`, `English (United States)` language, Altered Content `No`, Tags, and post-publish owner discussion comments)
- Enabling storefront sections (`Show Home tab.`, `For you`, `Short videos`, `Created playlists`), `150x150` Subscribe branding watermarks, and channel-wide `Not Made for Kids` defaults
- Running closed-loop analytics scraping, unresponded comment inbox triage, FFmpeg loudness/9:16 audits, and scheduled US prime-time uploads

## Core 7-Pillar Architecture

See [references/7-pillars-playbook.md](references/7-pillars-playbook.md) for the full creator checklist:

| Pillar | What It Automates / Enforces | Script / Reference |
|---|---|---|
| **1. Eligibility & Legal AdSense** | Audits Feature Eligibility (Standard / Intermediate SMS / Advanced KYC) & protects legal Country of Residence | `scripts/yt_channel_manager.py`, [references/high-rpm-usa-monetization.md](references/high-rpm-usa-monetization.md) |
| **2. Pro Storefront** | Generates `2560x1440` safe-zone banner, `800x800` avatar & `150x150` Subscribe watermark; turns ON `Home tab` & channel COPPA | `scripts/build_channel_branding.py`, `scripts/yt_channel_manager.py` |
| **3. Media & Policy Gate** | Checks `1080x1920`, `<=60s`, FFmpeg `volumedetect` (`-38` to `-3 dBFS`), title `<=60c`, `#Shorts`, transformative context | `scripts/media_loudness_validator.py` |
| **4. Complete Video Metadata** | Assigns series Playlist, Altered Content `No`, `Gaming` category, official Game Title, `English (United States)` language, Tags | `scripts/yt_studio_shorts_uploader.py` |
| **5. Community & Comments** | Posts & tries pinning curated discussion question + CTA per Short; checks `Studio -> Comments -> Unresponded` | `scripts/yt_channel_manager.py` |
| **6. EST/PST Scheduling** | Targets US morning (`9:00 AM EST`) and lunch (`12:15 PM EST`) windows with `msvcrt` lock + same-day dedup | `scripts/youtube_shorts_daily_pipeline.py`, `scripts/setup_windows_scheduler.ps1` |
| **7. Closed Analytics Loop** | Scrapes Dashboard + Content -> Shorts metrics + Earn thresholds into timestamped analytics history | `scripts/yt_channel_manager.py` |

## Quick Commands

```bash
# 1. Configure your channel without hardcoding secrets
cp examples/config.example.json config.json
cp examples/catalog.example.json queue/catalog.json

# 2. Generate pro 2560x1440 banner, 800x800 logo, and 150x150 Subscribe watermark
python scripts/build_channel_branding.py --title "YOUR CHANNEL" --subtitle "4K CLIPS | DAILY SHORTS"

# 3. Audit all queued Shorts (9:16, <60s, FFmpeg audio loudness, full metadata)
python scripts/youtube_shorts_daily_pipeline.py --verify

# 4. Apply Home Tab, Watermark, COPPA default, live video backfill & audit in Studio
python scripts/youtube_shorts_daily_pipeline.py --optimize-live

# 5. Run live daily ops upload (Analytics + Comments + Upload + Owner CTA Comment)
python scripts/youtube_shorts_daily_pipeline.py --slot morning --daily-ops
```

## Configuration

All scripts read from a single `config.json` (or `$YT_PRO_HOME/config.json`). See `examples/config.example.json` for the full template with every configurable field. The upload queue lives in `examples/catalog.example.json`.

## Hard Boundaries & Safety

- **Never bypass auth/KYC gates:** Stops cleanly if `accounts.google.com`, Chrome OTP, or Instagram checkpoint appears. Never spoof AdSense country to bypass ID/PAN/tax residency (`W-8BEN`).
- **Studio Polymer UI rules:** See [references/studio-cdp-selectors.md](references/studio-cdp-selectors.md) before modifying Playwright selectors (`:visible` menu filtering, `bounding_box` clicks, `Escape` backdrop dismissal, separate watch tab for comments).
- **Instagram optional pipeline:** Keep Hindi/regional feeds on dedicated IG/regional channels rather than mixing languages into a Tier-1 US YouTube feed ([references/instagram-dual-reel-sync.md](references/instagram-dual-reel-sync.md)).
- **Single-instance locks:** Cross-platform `msvcrt`/`fcntl` file locks prevent concurrent pipeline runs.
- **Tab leak prevention:** All CDP pages wrapped in `try...finally: await pg.close()` to prevent Chrome memory exhaustion.
