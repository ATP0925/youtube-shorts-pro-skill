# Changelog

All notable changes to `youtube-shorts-pro-skill` are documented here.

## [3.2.0] — 2026-11-26

### Added
- `scripts/copyright_free_shorts_factory.py` — Multi-category 100% copyright-free Shorts generator covering 7 top global viral niches (`Space & Science`, `Optical Illusions`, `Food Science`, `Human Body & Psychology`, `Tech & AI`, `Weird History`, `Wealth Math`) using `edge-tts` WordBoundary sync, procedural 60FPS animations, NASA PD / Openverse CC0 visuals, and FFmpeg synthesized audio (-14 LUFS).
- `references/copyright-free-monetization-niches.md` — Global high-view copyright-free niche architecture & YPP 2025/2026 Inauthentic Content compliance guide.

### Changed
- Made `media_loudness_validator.py`, `yt_channel_manager.py`, `yt_studio_shorts_uploader.py`, and `youtube_shorts_daily_pipeline.py` strictly **multi-niche capable**: per-video YouTube Studio `category` overrides work across `Science & Technology`, `Education`, `Entertainment`, `Howto & Style`, and `Gaming`, and `game_title` is only required/applied for `Gaming`.
- Added `edge-tts>=6.1.0` to `requirements.txt` and `pyproject.toml`.

## [3.1.0] — 2026-11-26

### Added
- `scripts/viral_hook_analyzer.py` — Deterministic FFmpeg viral readiness analyzer scoring 0–100 across 9:16 format, 0–3s hook audio energy vs. clip mean loudness, opening black-frame detection (`blackdetect`), visual pacing / cuts-per-minute (`scenedetect`), and duration sweet spot (`15–35s`).
- `scripts/auto_subtitle_styler.py` — Production-grade ASS kinetic subtitle generator (1080×1920 safe zone `MarginV=520`, Whisper JSON chunking, rotating keyword highlight colors) + FFmpeg -14 LUFS vertical renderer.
- `build_shorts_cover()` & `--cover-input` / `--cover-text` / `--cover-out` CLI in `scripts/build_channel_branding.py` for dual YouTube 4:5 + Instagram 1:1 center safe-zone 3-word cover overlays.
- `--viral-check` integration in `scripts/media_loudness_validator.py` and `scripts/youtube_shorts_daily_pipeline.py`.

### Fixed
- **US Eastern Broadcast-Day Deduplication (`_broadcast_day`):** Scheduled slot dedup in `scripts/youtube_shorts_daily_pipeline.py` now rolls over at 06:00 local time instead of midnight IST, preventing late-night catch-up uploads (e.g. `01:03 IST`) from falsely blocking that evening's `19:30 IST` / `22:45 IST` US prime-time slots.
- **IPv4 CDP Priority (`resolve_cdp_url` & `CDP_DEFAULT_URL`):** Defaults to `http://127.0.0.1:9222` and resolves `localhost` -> `127.0.0.1` first so Playwright does not hang on Windows IPv6 `::1`.

## [3.0.0] — 2026-11-26

### Added
- **Viral Video Creation Knowledge** — 4 new comprehensive reference documents:
  - `references/viral-hooks-retention.md` — Hook psychology (Cognitive Dissonance, Loss Aversion, Zeigarnik Effect, Identity Call-Out), multisensory hook execution, mid-video retention techniques, loop-back endings, hook templates for gaming channels, retention killers.
  - `references/editing-tools-automation.md` — Full tool comparison (CapCut, FFmpeg, Remotion, DaVinci Resolve, After Effects), FFmpeg advanced filters (vertical conversion, speed ramp, Ken Burns zoom, overlays, ASS subtitles), Whisper AI transcription pipeline, pro ASS subtitle template, sound design layer (whoosh/impact/riser/blip/drop/silence), complete automated pipeline diagram, free SFX/music sources.
  - `references/algorithm-signals.md` — YouTube Shorts algorithm (swipe-away rate, completion rate, loop rate, shares, saves, distribution tiers), Instagram Reels algorithm (DM shares as #1 signal), TikTok algorithm (interest-graph, semantic parsing), cross-platform signal comparison matrix, optimal duration by platform, anti-pattern list.
  - `references/thumbnail-cover-optimization.md` — Cover frame design rules (3-word max, single focal point, safe zone placement), pixel-level margin specs, first frame alignment, gaming-specific cover strategies, color psychology, FFmpeg cover extraction commands, Instagram grid optimization, dual-safe cover design.

### Changed
- `SKILL.md` — v3.0.0 rewrite: expanded from 7-pillar to 10-pillar architecture, added viral video creation sections (hook types, editing techniques, algorithm targets, CPM targets, pipeline flow), 25 trigger keywords, full reference index table, editing tool selection guide.

## [2.0.0] — 2026-11-26

### Added
- `pyproject.toml` — Project metadata (`requires-python >= 3.10`) and Ruff lint/isort config.
- `scripts/constants.py` — Centralized magic numbers, timeouts, thresholds, DOM selectors (`StudioSelectors`, `IGSelectors`), auth gate patterns.
- `scripts/exceptions.py` — Full exception hierarchy: `YTProError` base → 11 specific exceptions (`AuthGateError`, `CDPConnectionError`, `IGSafetyError`, `FFmpegNotFoundError`, `UploadError`, etc.).
- `scripts/logger.py` — `get_logger(__name__)` with `RotatingFileHandler` (5 MB × 3 backups).
- `scripts/__init__.py` — Package init with `__all__` listing 10 public modules.
- `references/troubleshooting.md` — 10 common issues with root causes and fixes.
- `CHANGELOG.md` — This file.
- `CONTRIBUTING.md` — Dev setup, code style, verification, and PR process.
- `.github/workflows/lint.yml` — CI: `py_compile`, `ruff check`, module imports, JSON validation, and `SKILL.md` verification on push/PR.
- `examples/README.md` — Complete field-by-field schema reference for `config.example.json` and `catalog.example.json`.

### Changed
- **Every Python script** rewritten with:
  - `from __future__ import annotations`
  - `__all__` exports
  - Full type annotations and docstrings
  - Structured logging via `logger.py` (no `print()`)
  - Constants from `constants.py` (no magic numbers)
  - Custom exceptions from `exceptions.py`
  - `StudioSelectors` / `IGSelectors` for DOM selectors
- `SKILL.md` — v2.0.0 rewrite: proper YAML triggers (12 keywords), troubleshooting section, limitations.
- `README.md` — Mermaid architecture diagram, 7-pillars table, CLI reference, FAQ.
- `run_slot.bat` — Timestamp logging, Python availability check, error level reporting.
- `setup_windows_scheduler.ps1` — `-Help` switch, time format validation, colored output.

### Fixed
- Walrus operator syntax error in `yt_studio_shorts_uploader.py` import block.
- Duplicate logic across modules consolidated into shared constants/helpers.

## [1.1.0] — 2026-11-25

### Added
- Portable skill structure with `SKILL.md`, `references/`, `examples/`.
- `yt_channel_manager.py` — Full Studio CDP automation (branding, watermark, settings, comments).
- `ig_reels_publisher.py` — Instagram Web Reels publisher via CDP.
- `media_loudness_validator.py` — FFmpeg-based audio loudness QA.
- `build_channel_branding.py` — Pillow banner/avatar/watermark generator.
- `youtube_shorts_daily_pipeline.py` — Orchestrator with morning/night slot scheduling.
- `config_loader.py` — JSON config with `.channel_state.json` persistence.
- `run_slot.bat` and `setup_windows_scheduler.ps1` — Windows Task Scheduler integration.

## [1.0.0] — 2026-11-21

### Added
- Initial knowledge-only skill (`youtube-pro-channel-ops`).
- Reference docs: 7-pillars playbook, high-RPM USA monetization, Studio CDP selectors.
