# Examples — Configuration & Catalog Reference

This directory contains template configuration files for `youtube-shorts-pro-skill`.

## 1. `config.example.json`

Copy to `config.json` in your working directory (or `$YT_PRO_HOME/config.json`). Any omitted or `null` field falls back to `DEFAULT_CONFIG` in `scripts/config_loader.py`.

| Field | Type | Default | Description |
|---|---|---|---|
| `channel_id` | string \| null | `null` | Target YouTube channel ID (`UC...`) |
| `channel_name` | string | `"Your Gaming Channel"` | Display name used for brand-account identity checks |
| `channel_handle` | string | `""` | Channel handle (`@YourHandle`) |
| `cdp_url` | string | `"http://localhost:9222"` | Chrome remote debugging HTTP endpoint |
| `target_audience` | string | `"USA / Tier-1 English"` | Audience target label for reporting |
| `video_language` | string | `"English (United States)"` | Value selected in Studio Video & Title/Desc language dropdowns |
| `default_category` | string | `"Gaming"` | Category selected inside Studio Show More |
| `default_game_title` | string | `"Grand Theft Auto VI"` | Official game title selected via Studio autocomplete |
| `playlists` | array[string] | 2 sample playlists | Default series playlists on the channel |
| `morning_window_hours` | array[int, int] | `[18, 21]` | Allowed hour range (`[start, end]` in local time) for scheduled morning runs |
| `night_window_start_hour` | int | `21` | Start hour (coupled with minute threshold `30`) for scheduled night runs |
| `ig_profile_url` | string | `"https://www.instagram.com/"` | Target Instagram profile URL for Reels publishing |
| `catalog_path` | string | `"queue/catalog.json"` | Path to upload queue catalog |
| `history_path` | string | `"youtube_shorts_history.json"` | Upload history & daily slot dedup ledger |
| `channel_state_path` | string | `"youtube_channel_state.json"` | Auto-updated active channel identity state |
| `audit_path` | string | `"youtube_channel_audit.json"` | Latest Studio Analytics + Eligibility snapshot |
| `analytics_history_path` | string | `"youtube_analytics_history.json"` | Rolling list (last 60) of audit snapshots |
| `comments_log_path` | string | `"youtube_comments_log.json"` | Latest Studio inbox comment replies |
| `watermark_path` | string | `"assets/watermark_150.png"` | 150×150 branding subscribe watermark PNG |

## 2. `catalog.example.json`

Copy to `queue/catalog.json` (or whatever `catalog_path` points to). Each item in the JSON array has:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique slug used for history deduplication |
| `slot` | `"morning"` \| `"night"` | Yes | Preferred scheduling wave (`_select_next_short` prefers matching slot first) |
| `video_path` | string | Yes | Local path to vertical 9:16 `.mp4` clip (≤60s) |
| `youtube_shorts` | object | Yes | Nested Studio metadata block (see below) |

### Nested `youtube_shorts` fields

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Short title (`<= 60` chars recommended, must contain `#Shorts`) |
| `description` | string | Yes | Description text with hashtags & CTA |
| `tags` | array[string] | No | 8–12 clean niche tags |
| `playlist_name` | string | Yes | Exact playlist title to assign during upload |
| `game_title` | string | Yes | Official game title for Gaming category autocomplete |
| `altered_content` | bool | No | `true` only for photorealistic synthetic AI media (default `false`) |
| `pinned_comment` | string | Yes | Owner discussion CTA posted & pinned after Public publish |

## 3. Auto-Generated State & Logs (Do Not Commit)

- `youtube_channel_state.json` — Active `channel_id`, `channel_name`, and `handle` discovered or loaded by `yt_channel_manager.py`.
- `youtube_shorts_history.json` — Records `last_morning`, `last_night`, and per-upload `{id, slot, title, video_id, video_url, datetime, status}`.
- `logs/yt_pro.log` — Rotating log file (5 MB × 3 backups).
