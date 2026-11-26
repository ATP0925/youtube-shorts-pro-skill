---
name: youtube-shorts-pro-skill
description: >-
  Use when setting up, optimizing, auditing, or automating a YouTube Shorts
  or high-RPM US-audience gaming channel — including viral video creation,
  editing techniques, hook psychology, algorithm optimization, Studio CDP uploads,
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
    - viral video creation
    - viral hooks retention
    - video editing techniques
    - short form content
    - speed ramp motion blur
    - subtitle caption styling
    - algorithm signals
    - thumbnail cover frame
    - sound design sfx
    - loop ending retention
    - capcut ffmpeg remotion
    - whisper transcription
    - gaming clip editing
  author: ATP0925
  version: "3.1.0"
---

# YouTube Shorts Pro Skill

Complete AI-agent operating system for **creating, editing, optimizing, and automating** viral YouTube Shorts targeting Tier-1 USA/English RPM, with optional Instagram Reels and TikTok cross-posting.

## When to Use

- **Creating viral short-form content** — hook psychology, pacing, retention engineering, loop endings
- **Editing gaming clips** — speed ramps, motion blur, sound design, viral caption styles
- Building or rebranding a YouTube Shorts channel to perform like a top creator
- Optimizing toward USA / UK / CA / AU high-RPM English viewers
- Automating YouTube Studio uploads via Chrome CDP with complete pro metadata
- Running closed-loop analytics, comment inbox triage, FFmpeg media audits
- Understanding platform algorithms (YouTube Shorts, Instagram Reels, TikTok)

---

## Architecture Overview

### The 10-Pillar System

| # | Pillar | Reference / Script |
|---|--------|--------------------|
| 1 | **Viral Hook Psychology** | `viral_hook_analyzer.py`, [viral-hooks-retention.md](references/viral-hooks-retention.md) |
| 2 | **Editing & Automation Pipeline** | `auto_subtitle_styler.py`, [editing-tools-automation.md](references/editing-tools-automation.md) |
| 3 | **Platform Algorithm Signals** | [references/algorithm-signals.md](references/algorithm-signals.md) |
| 4 | **Thumbnail & Cover Optimization** | `build_channel_branding.py --cover-input`, [thumbnail-cover-optimization.md](references/thumbnail-cover-optimization.md) |
| 5 | Eligibility & Legal AdSense | `yt_channel_manager.py`, [7-pillars-playbook.md](references/7-pillars-playbook.md) |
| 6 | Pro Storefront (Banner/Avatar/Watermark) | `build_channel_branding.py`, `yt_channel_manager.py` |
| 7 | Media & Policy Gate (9:16, ≤60s, loudness) | `media_loudness_validator.py --viral-check` |
| 8 | Complete Video Metadata | `yt_studio_shorts_uploader.py` |
| 9 | EST/PST Dual-Slot Scheduling | `youtube_shorts_daily_pipeline.py` |
| 10 | Closed Analytics Loop | `yt_channel_manager.py` |

---

## Viral Video Creation (Pillars 1-4)

### The Viral Short Anatomy

```
SEC 0-1:  VISUAL SHOCK + TEXT-ON-SCREEN + BASS HIT
SEC 1-3:  PSYCHOLOGICAL HOOK (contrarian / loss aversion / open loop)
SEC 3-8:  RAPID PACING (visual pattern interrupt every 2.5-4 seconds)
SEC 8-15: VALUE DELIVERY (the promise from the hook)
SEC 15-25: MICRO-CLIFFHANGERS + PEAK ACTION (speed ramps, slow-mo)
SEC 25-30: PAYOFF + LOOP-BACK ENDING (seamless → loops to SEC 0)
```

### Hook Types (ranked by power)

| Type | Template | Psychology |
|------|----------|-----------|
| Contrarian | "Everyone uses [X] but [Y] is actually better" | Cognitive dissonance |
| Loss Aversion | "Stop doing [X] — you're wasting [Y]" | 2× loss > gain motivation |
| Open Loop | "This happened on day 3..." | Zeigarnik Effect (crave closure) |
| Identity Call | "If you're a [demographic], watch this" | Self-relevance filter |
| Secret/Hidden | "They don't want you to find this" | Forbidden knowledge |

→ Full hook library: [references/viral-hooks-retention.md](references/viral-hooks-retention.md)

### Editing Techniques

| Technique | When | Tool |
|-----------|------|------|
| **Speed Ramp** | Action peak (drift, jump, crash) | FFmpeg `setpts` / CapCut curves |
| **Motion Blur** | High-speed movement | RSMB plugin / FFmpeg `minterpolate` |
| **Kinetic Captions** | Word-by-word subtitle highlight | ASS styling / CapCut auto-captions |
| **Sound Design** | Every transition, zoom, impact | Layered SFX (whoosh, impact, riser) |
| **Audio Ducking** | When SFX or VO plays | Lower music, raise SFX |
| **Loop-Back End** | Last 2 seconds | Edit ending to flow into beginning |
| **Ken Burns Zoom** | Static images → motion | FFmpeg `zoompan` filter |

→ Full editing guide: [references/editing-tools-automation.md](references/editing-tools-automation.md)

### Algorithm Optimization Targets

| Signal | YouTube Shorts | Instagram Reels | Target |
|--------|---------------|----------------|--------|
| Swipe-Away Rate | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | < 30% |
| Completion Rate | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | > 90% |
| Loop/Replay | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | > 100% AVD |
| Shares | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Drive "you have to see this" |
| Saves | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Utility/education content |

→ Full signal analysis: [references/algorithm-signals.md](references/algorithm-signals.md)

### Cuts Per Minute (CPM) Targets

| Content Type | Target CPM |
|-------------|------------|
| Gaming montage | 30-50+ |
| Tutorial/guide | 20-35 |
| Story/narrative | 15-25 |
| Satisfying loop | 10-15 |

---

## Channel Operations (Pillars 5-10)

### Quick Commands

```bash
cp examples/config.example.json config.json        # Configure
python scripts/build_channel_branding.py --title "CHANNEL NAME"  # Brand
python scripts/build_channel_branding.py --cover-input frame.jpg --cover-text "FASTEST CAR" --cover-out cover.png
python scripts/viral_hook_analyzer.py --catalog queue/catalog.json  # Viral Score
python scripts/auto_subtitle_styler.py --whisper-json subs.json --render-input raw.mp4 --render-output out.mp4
python scripts/youtube_shorts_daily_pipeline.py --verify --viral-check  # Validate
python scripts/youtube_shorts_daily_pipeline.py --optimize-live   # Setup Studio
python scripts/youtube_shorts_daily_pipeline.py --slot morning --daily-ops  # Upload
```

### Configuration

All scripts read from `config.json` (or `$YT_PRO_HOME/config.json`). See [examples/README.md](examples/README.md) for field documentation.

---

## Editing Tool Selection Guide

| Scenario | Recommended Tool |
|----------|-----------------|
| One-off creative edit with trendy captions | **CapCut** |
| Automated daily pipeline (batch 50+ videos) | **FFmpeg + Whisper AI** |
| Programmatic SaaS / template-based generation | **Remotion** |
| Complex VFX / motion graphics | **After Effects** |
| Professional color grading | **DaVinci Resolve** |

→ Full tool comparison: [references/editing-tools-automation.md](references/editing-tools-automation.md)

---

## Automated Pipeline Flow

```
RAW CLIP (Rockstar Editor / Screen Capture)
  → Whisper AI (word-level transcription → JSON/SRT)
    → Python Styler (viral ASS subtitle formatting)
      → FFmpeg Master Filter:
          • Vertical 1080×1920 conversion
          • Speed ramp at action peaks
          • Burn ASS subtitles
          • Audio normalization (-14 LUFS)
          • Mix background music (ducked)
          • Overlay watermark
        → Media Validator (resolution / duration / loudness)
          → Catalog Entry (title, tags, playlist, game title)
            → CDP Uploader (YouTube Studio / Instagram)
              → Post-Publish (owner CTA comment + analytics scrape)
```

---

## Hard Boundaries & Safety

- **Never bypass auth/KYC gates** — raises `AuthGateError` and stops cleanly
- **Never spoof AdSense country** — legal residence must be real
- **Studio Polymer UI rules** — see [references/studio-cdp-selectors.md](references/studio-cdp-selectors.md)
- **Single-instance locks** — cross-platform `msvcrt`/`fcntl` file locks
- **Tab leak prevention** — all CDP pages in `try...finally: await pg.close()`

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for solutions to common issues.

## Limitations

- Requires Chrome running with `--remote-debugging-port=9222` (manual setup)
- Intermediate/Advanced feature eligibility requires manual phone OTP / video KYC
- Instagram publishing requires an active logged-in session in Chrome
- Not a replacement for genuine creative vision — automation handles distribution and formatting

---

## All References

| Reference | Topic |
|-----------|-------|
| [viral-hooks-retention.md](references/viral-hooks-retention.md) | Hook psychology, retention loops, pattern interrupts, hook templates |
| [editing-tools-automation.md](references/editing-tools-automation.md) | FFmpeg, Whisper, CapCut, Remotion, ASS styling, sound design, pipeline |
| [algorithm-signals.md](references/algorithm-signals.md) | YT Shorts / IG Reels / TikTok algorithm signals, distribution tiers |
| [thumbnail-cover-optimization.md](references/thumbnail-cover-optimization.md) | Cover frame design, safe zones, text overlay, gaming strategies |
| [7-pillars-playbook.md](references/7-pillars-playbook.md) | Channel operations checklist (eligibility, storefront, metadata) |
| [high-rpm-usa-monetization.md](references/high-rpm-usa-monetization.md) | RPM benchmarks, YPP tiers, Form W-8BEN |
| [instagram-dual-reel-sync.md](references/instagram-dual-reel-sync.md) | Reels cross-posting & anti-spam rules |
| [studio-cdp-selectors.md](references/studio-cdp-selectors.md) | Studio Polymer UI DOM selectors |
| [troubleshooting.md](references/troubleshooting.md) | Common issues and fixes |
