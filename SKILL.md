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
    - ffmpeg loudness
    - shorts feed algorithm
  author: ATP0925
  version: "2.0.0"
---

# YouTube Shorts Pro Skill

Complete AI-agent operating system for building, upgrading, auditing, and running a monetizable YouTube Shorts channel targeting Tier-1 USA/English RPM, with optional Instagram Reels dual-slot cross-posting.

## When to Use

- Building or rebranding a YouTube Shorts channel to look and perform like a top creator
- Optimizing toward USA / UK / CA / AU high-RPM English viewers while preserving local AdSense payouts (India PAN + Form `W-8BEN`)
- Automating YouTube Studio uploads via Chrome CDP with **complete pro metadata** (Playlists, `Gaming` category, official `Game title`, `English (United States)` language, Altered Content, Tags, Owner CTA Comments)
- Enabling storefront sections (Home Tab, Subscribe watermark, channel-wide COPPA)
- Running closed-loop analytics, comment inbox triage, FFmpeg media audits, and scheduled US prime-time uploads

## Core 7-Pillar Architecture

See [references/7-pillars-playbook.md](references/7-pillars-playbook.md) for the full checklist.

| # | Pillar | Script |
|---|--------|--------|
| 1 | Eligibility & Legal AdSense | `yt_channel_manager.py` |
| 2 | Pro Storefront (Banner/Avatar/Watermark/Home Tab/COPPA) | `build_channel_branding.py`, `yt_channel_manager.py` |
| 3 | Media & Policy Gate (9:16, ≤60s, loudness, title) | `media_loudness_validator.py` |
| 4 | Complete Video Metadata | `yt_studio_shorts_uploader.py` |
| 5 | Community & Pinned Comments | `yt_channel_manager.py` |
| 6 | EST/PST Dual-Slot Scheduling | `youtube_shorts_daily_pipeline.py` |
| 7 | Closed Analytics Loop | `yt_channel_manager.py` |

## Quick Commands

```bash
cp examples/config.example.json config.json        # Configure
python scripts/build_channel_branding.py --title "CHANNEL NAME"  # Brand
python scripts/youtube_shorts_daily_pipeline.py --verify          # Validate
python scripts/youtube_shorts_daily_pipeline.py --optimize-live   # Setup Studio
python scripts/youtube_shorts_daily_pipeline.py --slot morning --daily-ops  # Upload
```

## Configuration

All scripts read from `config.json` (or `$YT_PRO_HOME/config.json`). See [examples/README.md](examples/README.md) for field documentation.

## Hard Boundaries & Safety

- **Never bypass auth/KYC gates** — raises `AuthGateError` and stops cleanly
- **Never spoof AdSense country** — legal residence must be real
- **Studio Polymer UI rules** — see [references/studio-cdp-selectors.md](references/studio-cdp-selectors.md)
- **Single-instance locks** — cross-platform `msvcrt`/`fcntl` file locks
- **Tab leak prevention** — all CDP pages in `try...finally: await pg.close()`

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for solutions to common issues (CDP refused, auth gates, FFmpeg missing, backdrop blocking, etc.).

## Limitations

- Requires Chrome running with `--remote-debugging-port=9222` (manual setup)
- Intermediate/Advanced feature eligibility requires manual phone OTP / video KYC
- Instagram publishing requires an active logged-in session in Chrome
- Not a replacement for genuine content creation — automation handles distribution only

## Related References

- [references/high-rpm-usa-monetization.md](references/high-rpm-usa-monetization.md) — RPM benchmarks, YPP tiers, Form `W-8BEN`
- [references/instagram-dual-reel-sync.md](references/instagram-dual-reel-sync.md) — Optional Reels cross-posting & anti-spam rules
