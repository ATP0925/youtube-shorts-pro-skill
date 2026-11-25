# Changelog

All notable changes to `youtube-shorts-pro-skill` are documented here.

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
