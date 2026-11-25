# Troubleshooting Guide

Common issues and fixes for the youtube-shorts-pro-skill pipeline.

---

## 1. CDP Connection Refused

**Symptom:** `CDPConnectionError: Cannot reach http://localhost:9222`

**Root Cause:** Chrome isn't running with remote debugging enabled.

**Fix:**
```bat
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data"
```
> Ensure no other Chrome instance is using that profile. Close all Chrome windows first.

---

## 2. Google Auth Gate Triggered

**Symptom:** Script stops with `AuthGateError: Google requires manual verification`

**Root Cause:** Google detected automation and is asking "Verify it's you" or 2-Step Verification.

**Fix:**
1. Open Chrome manually and complete the verification.
2. After logging in, navigate to `studio.youtube.com` to confirm access.
3. Re-run the script.

> The scripts **never** attempt to bypass auth challenges — this is by design for account safety.

---

## 3. Backdrop Blocking Clicks

**Symptom:** Click actions fail silently or hit `tp-yt-iron-overlay-backdrop.opened`.

**Root Cause:** YouTube Studio shows overlay backdrops (modals, notifications) that intercept clicks.

**Fix:** The `yt_channel_manager.py` has `_dismiss_backdrops()` which handles this automatically. If you encounter it in a custom flow:
```python
backdrop = page.locator("tp-yt-iron-overlay-backdrop.opened")
if await backdrop.count() > 0:
    await backdrop.click()
    await page.wait_for_timeout(500)
```

---

## 4. FFmpeg Not Found

**Symptom:** `FFmpegNotFoundError: ffmpeg binary not found in PATH`

**Root Cause:** FFmpeg is not installed or not in the system PATH.

**Fix:**
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, add `bin/` to PATH.
- **Verify:** `ffmpeg -version` should return version info.

---

## 5. Upload Stuck at "Processing"

**Symptom:** Script times out waiting for the publish confirmation dialog.

**Root Cause:** YouTube is still processing the video server-side. Longer videos or high-traffic times cause delays.

**Fix:**
- Increase `UPLOAD_CONFIRM_MAX_POLLS` in `constants.py` (default: 30 × 2s = 60s).
- Check YouTube Studio manually — the video may have published successfully.
- Ensure the video is under 60 seconds (Shorts limit).

---

## 6. Category Not Set to Gaming

**Symptom:** Video publishes but category shows "People & Blogs" instead of "Gaming".

**Root Cause:** The category dropdown didn't expand or the "Gaming" option wasn't found.

**Fix:**
- Ensure `StudioSelectors.CATEGORY_TRIGGER` matches your Studio version.
- Check that the page has fully loaded before clicking "Show more".
- Look at logs: `log.warning("Category dropdown did not expand")` indicates the selector changed.

---

## 7. Comment Section Not Loading

**Symptom:** `post_and_pin_comment()` fails — comment box not found on watch page.

**Root Cause:** The Shorts watch page requires scrolling to load the comment section.

**Fix:**
- The function already scrolls to `#comments`. If it still fails:
  - Wait longer (increase the scroll-and-wait loop count).
  - Some videos may have comments disabled by YouTube's spam filter initially.

---

## 8. Wrong Channel Identity

**Symptom:** Uploads go to the wrong channel (personal vs brand account).

**Root Cause:** Chrome is logged into multiple YouTube channels.

**Fix:**
1. Set `channel_id` in your `config.json` to the correct `UC...` ID.
2. The pipeline uses `load_channel_state()` to track which channel is active.
3. If needed, manually switch channels in YouTube Studio before running.

---

## 9. Scheduled Task Not Running

**Symptom:** Windows Task Scheduler shows "Ready" but the task never fires.

**Root Cause:** Laptop is asleep/hibernated at the scheduled time, or battery saver blocks it.

**Fix:**
- In `setup_windows_scheduler.ps1`, the `-AllowStartIfOnBatteries` and `-StartWhenAvailable` flags are already set.
- Check Task Scheduler → History tab for error codes.
- Run `run_slot.bat morning` manually to verify the script works.
- Ensure Python is in the system PATH.

---

## 10. Instagram Action Blocked

**Symptom:** `IGSafetyError: Suspension indicator detected: "action blocked"`

**Root Cause:** Instagram rate-limited the account for too many actions.

**Fix:**
1. **Stop all automation immediately** — wait 24-48 hours.
2. Do NOT try to log in repeatedly.
3. After cooldown, post manually once to verify the account is active.
4. Resume automation with longer delays between posts.

> The script uses `IG_SUSPENSION_INDICATORS` to detect these blocks early and stop safely.
