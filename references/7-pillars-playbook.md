# The 7 Pillars of Running a Real Pro YouTube Shorts Channel

Never treat YouTube automation as `"upload MP4 -> done"`. Sustainable growth and YouTube Partner Program (YPP) approval depend on running all 7 creator systems continuously.

---

## Pillar 1: Trust, Feature Eligibility & Account Compliance
Check `YouTube Studio -> Settings -> Channel -> Feature eligibility`:
1. **Standard features (`Enabled`):** Video uploads, playlist creation, adding videos to playlists.
2. **Intermediate features (`Phone SMS`):** Videos > 15 minutes, custom thumbnails, live streaming. Must be verified manually by phone OTP.
3. **Advanced features (`History / Video / ID KYC`):** Higher daily upload limits, pinned comments / external links eligibility, and full YPP application eligibility.

Also confirm **2-Step Verification (2SV)** is enabled on the Google account before applying to YPP.

---

## Pillar 2: High-Trust Storefront (`Customisation`)
1. **Banner (`2560x1440`):** Keep primary text strictly inside the `1546x423` center safe zone so mobile, desktop, and TV crops never clip letters.
2. **Avatar (`800x800`):** High-contrast vector/emblem logo legible down to `48px` mobile circle.
3. **Video Watermark (`150x150`):** Explicit dark badge with vibrant `SUBSCRIBE` bar placed via `Entire video` display mode.
4. **Home Tab ON (`Show Home tab.`):** Expose `For you`, `Short videos`, `Videos`, and `Created playlists` shelves on `/channel/<ID>`.
5. **Channel-wide COPPA (`Advanced settings`):** Lock `No, set this channel as not Made for Kids` so every Short inherits personalized ads, notifications, and comments.
6. **Language Isolation:** Never mix regional/non-English Shorts onto a channel built for USA/UK English seed distribution—keep non-English videos `Unlisted` or on a separate regional channel.

---

## Pillar 3: Shorts Feed Algorithm & Anti-Reused-Content Quality Gate
- **Viewed vs. Swiped Away (`VVSA`):** Target `> 70%` viewed / `< 30%` swiped away using an unmistakable `< 2s` visual + caption hook.
- **Average Percentage Viewed (`APV`):** Keep pacing tight (`20s - 35s`), remove dead air, loop cleanly, and keep subtitles above bottom `350px` and left of right `160px` YouTube UI overlays.
- **Audio Loudness:** Validate FFmpeg `volumedetect` `mean_volume` between `-22 dBFS` and `-6 dBFS` (hard guard `-38` to `-3 dBFS`).
- **Anti-Reused / Inauthentic Policy Protection:** Raw re-uploads get rejected at monetization review. Ensure every Short has transformative value: clean framing, synchronized captions, editorial stream/scene context, original hook packaging, and community prompts.

---

## Pillar 4: Full Per-Video Metadata Completeness
In every Upload Dialog & backfill pass:
1. Title `<= 60` characters with curiosity gap ending in `#Shorts` (avoids mobile truncation).
2. `Not Made for Kids` selected.
3. Assigned directly to its niche series Playlist (`Playlists -> Select`).
4. Expanded `Show more`:
   - `Altered content`: `No` for game graphics/gameplay (check `Yes` only for photorealistic synthetic AI scenes).
   - `Category`: `Gaming` -> unlock and select exact official **`Game title`** (e.g., `Grand Theft Auto VI`).
   - `Video language` & `Title and description language`: `English (United States)`.
   - Clean niche tags (8-12 tags, no spam stuffing).
   - Optional `Related video` funnel linking to an anchor Short/compilation.

---

## Pillar 5: Post-Upload Community & Pinned Comment Loop
- Immediately after a Short publishes, open its watch/Shorts page under the channel identity (not personal default profile) and post an engaging discussion question + subscribe CTA.
- Pin the owner comment whenever `Advanced Features` allows.
- Poll `Studio -> Community -> Comments -> Unresponded` on every scheduled run and reply concisely to real non-spam viewer comments.

---

## Pillar 6: Target-Timezone Prime-Time Scheduling
Upload synchronously to target viewer active hours (convert EST/PST peaks cleanly into host OS timezone):
- **US East Morning Scroll (`9:00 AM EST` / `6:00 AM PST`):** e.g., `19:30 IST`
- **US Lunch & Midday Peak (`12:15 PM EST` / `9:15 AM PST`):** e.g., `22:45 IST`
Enforce single-instance OS file locks (`msvcrt` on Windows / `fcntl` on POSIX), `--scheduled` window checks, and same-day duplicate protection.

---

## Pillar 7: Closed-Loop Analytics Feedback
Before selecting daily uploads, scrape Studio Dashboard, `Content -> Shorts`, and `Earn` counters into timestamped JSON history so winners guide topic priority instead of blind queue iteration.
