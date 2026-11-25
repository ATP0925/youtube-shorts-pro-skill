# YouTube Shorts Pro Skill

> A complete AI-agent operating system for building, upgrading, auditing, and running a monetizable YouTube Shorts channel — optimized for USA/Tier-1 English high-RPM audiences with optional Instagram Reels dual-slot cross-posting.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-CDP-green.svg)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What This Does

This skill automates the **7 core pillars** of running a professional YouTube Shorts channel through Chrome CDP + Playwright:

| # | Pillar | Automation |
|---|--------|------------|
| 1 | **Eligibility & Legal** | Audits Feature Eligibility tiers, protects AdSense residency |
| 2 | **Pro Storefront** | Generates banner/avatar/watermark, enables Home Tab & COPPA |
| 3 | **Media Quality Gate** | Validates 9:16, ≤60s, FFmpeg loudness, title length, metadata |
| 4 | **Complete Metadata** | Playlist, Gaming category, Game Title, US English, Tags, Altered Content |
| 5 | **Community Loop** | Posts & pins owner CTA comments, replies to unresponded inbox |
| 6 | **EST/PST Scheduling** | Dual US prime-time slots with file locks & dedup protection |
| 7 | **Analytics Feedback** | Scrapes Dashboard, Shorts metrics, Earn progress into JSON history |

## Architecture

```
youtube-shorts-pro-skill/
├── SKILL.md                          # AI agent skill definition (YAML frontmatter)
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── LICENSE                           # MIT License
├── .gitignore
├── examples/
│   ├── config.example.json           # Channel configuration template
│   └── catalog.example.json          # Upload queue template
├── references/
│   ├── 7-pillars-playbook.md         # Complete creator checklist
│   ├── high-rpm-usa-monetization.md  # RPM/CPM strategy & YPP milestones
│   ├── studio-cdp-selectors.md       # 9 Polymer DOM gotchas
│   └── instagram-dual-reel-sync.md   # Optional IG Reels guide
└── scripts/
    ├── config_loader.py              # Portable config & cross-platform file lock
    ├── build_channel_branding.py     # Avatar, Banner & Watermark generator
    ├── media_loudness_validator.py   # FFprobe + FFmpeg audio validator
    ├── yt_channel_manager.py         # Studio channel ops (Home Tab, Watermark, COPPA, Comments, Analytics)
    ├── yt_studio_shorts_uploader.py  # Full-metadata upload engine
    ├── youtube_shorts_daily_pipeline.py  # Master CLI orchestrator
    ├── ig_reels_publisher.py         # Instagram Reels CDP publisher
    ├── run_slot.bat                  # Windows batch launcher
    └── setup_windows_scheduler.ps1   # Windows Task Scheduler setup
```

## Prerequisites

- **Python 3.10+**
- **Google Chrome** running with remote debugging:
  ```bash
  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-yt-profile"
  ```
- **FFmpeg & FFprobe** in `PATH` (for media validation)
- A YouTube channel logged into Chrome with Studio access

## Quick Start

```bash
# 1. Clone
git clone https://github.com/ATP0925/youtube-shorts-pro-skill.git
cd youtube-shorts-pro-skill

# 2. Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# 3. Configure your channel
cp examples/config.example.json config.json
# Edit config.json with your channel_id, channel_name, etc.

cp examples/catalog.example.json queue/catalog.json
# Add your video entries to the catalog

# 4. Generate branding assets
python scripts/build_channel_branding.py --title "YOUR CHANNEL" --subtitle "4K CLIPS | DAILY SHORTS"

# 5. Validate all queued Shorts
python scripts/youtube_shorts_daily_pipeline.py --verify

# 6. Apply Studio foundation (Home Tab, Watermark, COPPA)
python scripts/youtube_shorts_daily_pipeline.py --optimize-live

# 7. Upload a Short with full metadata
python scripts/youtube_shorts_daily_pipeline.py --slot morning --daily-ops

# 8. Check channel status
python scripts/youtube_shorts_daily_pipeline.py --status
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `--verify` | Validate all catalog entries (resolution, duration, loudness, metadata) |
| `--audit` | Scrape Studio Analytics, Feature Eligibility, Earn progress & reply to comments |
| `--optimize-live` | Enable Home Tab + Watermark + COPPA + backfill metadata on live Shorts |
| `--slot morning\|night\|auto` | Select and upload next queued Short for the given time slot |
| `--daily-ops` | Run analytics + comments inbox before uploading |
| `--scheduled` | Mark as triggered by Task Scheduler (enables window & dedup checks) |
| `--dry-run` | Validate selection without uploading |
| `--count N` | Upload N Shorts in one run (default: 1) |
| `--status` | Print channel state and upload history summary |

## Automated Scheduling (Windows)

```powershell
# Register dual US prime-time tasks (default: 19:30 IST morning, 22:45 IST night)
powershell -ExecutionPolicy Bypass -File scripts/setup_windows_scheduler.ps1

# Custom times
powershell -File scripts/setup_windows_scheduler.ps1 -MorningTime "20:00" -NightTime "23:00" -TaskPrefix "MyChannel"
```

## Safety Guarantees

- **Never bypasses auth gates:** Stops cleanly on Google 2FA, CAPTCHA, Instagram checkpoints
- **Never spoofs AdSense country:** Legal residence must be real (use W-8BEN for tax treaty benefits)
- **Single-instance protection:** Cross-platform file locks prevent concurrent pipeline runs
- **Same-day dedup:** Scheduled runs skip if the slot already succeeded today
- **Tab leak prevention:** All CDP pages wrapped in `try...finally: await pg.close()`

## Using as an AI Agent Skill

Copy to your skills directory for Claude Code, Antigravity, or similar agents:

```bash
# Antigravity / Claude Code
cp -r . ~/.gemini/config/skills/youtube-shorts-pro-skill/
```

The agent will use this skill when it encounters triggers like: `youtube shorts`, `gaming channel`, `high rpm`, `cdp automation`, `youtube studio`, `adsense`, `instagram reels`.

## License

[MIT](LICENSE)
