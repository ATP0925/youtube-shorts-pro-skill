# The 7 Pillars of Running a Real Pro YouTube Shorts Channel

Never treat YouTube automation as `"upload MP4 -> done"`. Sustainable growth and YouTube Partner Program (YPP) approval depend on running all 7 creator systems continuously.

---

## Pillar 1: Trust, Feature Eligibility & Account Compliance
Check `YouTube Studio -> Settings -> Channel -> Feature eligibility`:
1. **Standard features (`Enabled`):** Video uploads, playlist creation, adding videos to playlists.
2. **Intermediate features (`Phone SMS`):** Videos > 15 minutes, custom thumbnails, live streaming. Verified manually via phone OTP.
3. **Advanced features (`History / Video / ID KYC`):** Higher daily upload limits, pinned comments / external links eligibility, and full YPP eligibility.

- **Targets:** All 3 tiers `Enabled` + **2-Step Verification (2SV)** enabled + `0` active Community Guidelines strikes.
- **Common Mistake:** Trying to automate around OTP/KYC gates or leaving `Advanced features` disabled (causes Owner comments not to pin reliably).

---

## Pillar 2: High-Trust Storefront (`Customisation`)
1. **Banner (`2560x1440`):** Keep primary text strictly inside the `1546x423` center safe zone so mobile, desktop, and TV crops never clip letters.
2. **Avatar (`800x800`):** High-contrast emblem legible down to `48px` mobile circle.
3. **Video Watermark (`150x150`):** Explicit dark badge with vibrant `SUBSCRIBE` bar placed via `Entire video` display mode.
4. **Home Tab ON (`Show Home tab.`):** Expose `For you`, `Short videos`, `Videos`, and `Created playlists` shelves on `/channel/<ID>`.
5. **Channel-wide COPPA (`Advanced settings`):** Lock `No, set this channel as not Made for Kids`.
6. **Language Isolation:** Keep 100% of Shorts in one target language per channel.

- **Targets:** `home_tab_enabled: true`, `watermark_uploaded: true`, `coppa_channel_set: true`.
- **Common Mistake:** Mixing Hindi/regional uploads onto a channel targeting US English RPM — confuses YouTube's seed distribution graph.

---

## Pillar 3: Shorts Feed Algorithm & Anti-Reused-Content Gate
- **Viewed vs. Swiped Away (`VVSA`):** Target `> 70%` viewed / `< 30%` swiped away using an unmistakable `< 2s` visual + caption hook.
- **Average Percentage Viewed (`APV`):** Target `> 90%` on `20s–35s` clips; eliminate dead air and loop ending into opening frame.
- **Subtitle Safe Margin:** Keep captions above bottom `350px` and left of right `160px` YouTube UI overlays.
- **Audio Loudness:** Mean volume between `-22 dBFS` and `-6 dBFS` (hard pipeline guard: `-38` to `-3 dBFS`).
- **Originality Policy:** Every Short must include transformative framing, clean synchronized captions, scene context, or editorial packaging.

- **Common Mistake:** Uploading quiet (`< -40 dBFS`), clipped (`> -2 dBFS`), or letterboxed landscape-in-portrait clips with subtitles hidden behind the description text.

---

## Pillar 4: Full Per-Video Metadata Completeness
In every Upload Dialog & backfill pass:
1. Title `<= 60` characters with curiosity gap ending in `#Shorts`.
2. `Not Made for Kids` selected.
3. Assigned directly to its niche series Playlist.
4. Expanded `Show more`:
   - `Altered content`: `No` for game engine footage (`Yes` only for photorealistic synthetic AI scenes).
   - `Category`: `Gaming` -> unlock and select exact official **`Game title`** (e.g., `Grand Theft Auto VI`).
   - `Video language` & `Title and description language`: `English (United States)`.
   - `8–12` relevant niche tags (`<= 450` chars combined).

- **Targets:** `100%` of live Shorts carry playlist + Gaming category + official Game Title + US English language.
- **Common Mistake:** Using YouTube Data API alone and leaving Category on `People & Blogs` or missing official `Game title` shelf indexing.

---

## Pillar 5: Post-Upload Community & Pinned Comment Loop
- Immediately after a Short publishes (`Public`), open its watch/Shorts page under the **brand channel identity** and post an engaging discussion question CTA.
- Pin the owner comment whenever `Advanced features` permits.
- Poll `Studio -> Community -> Comments -> Unresponded` on every scheduled run (`MAX_INBOX_REPLIES_PER_RUN = 3`, filtered by spam keywords).

- **Targets:** `< 24h` response time on non-spam comments; `100%` of new Public Shorts have an owner CTA comment.
- **Common Mistake:** Posting the comment from your personal Google profile instead of switching to the Brand Channel avatar first.

---

## Pillar 6: Target-Timezone Prime-Time Scheduling
Upload synchronously to target viewer active hours:
- **US East Morning Scroll (`9:00 AM EST` / `6:00 AM PST`):** `19:30 IST` (`morning` slot, allowed window `18:00–21:29`)
- **US Midday Peak (`12:15 PM EST` / `9:15 AM PST`):** `22:45 IST` (`night` slot, allowed `>= 21:30`)
Enforce OS file locks (`msvcrt`/`fcntl`), `--scheduled` window checks, and same-day dedup (`last_morning` / `last_night`).

- **Targets:** Maximum `2` Shorts/day spaced cleanly; `0` duplicate same-day slot runs.
- **Common Mistake:** Firing both uploads back-to-back or during midnight US hours (kills initial 1-hour Shorts shelf velocity).

---

## Pillar 7: Closed-Loop Analytics Feedback
Before selecting daily uploads, scrape Studio Dashboard, `Content -> Shorts`, and `Earn` counters into timestamped `youtube_analytics_history.json` (`<= 60` rolling snapshots) so winning hooks and playlists guide topic priority instead of blind queue iteration.

- **Common Mistake:** Publishing blindly for weeks without checking `VVSA` and subscriber conversion on winning Shorts formats.
