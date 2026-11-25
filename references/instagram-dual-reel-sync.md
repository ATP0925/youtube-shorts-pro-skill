# Optional Instagram Reels Dual-Slot Cross-Platform Guide

For regional audiences or companion traffic funneling back to YouTube, publish Instagram Reels via `scripts/ig_reels_publisher.py` using safe browser CDP automation.

## Dual Target Slots & Anti-Spam Cooldowns

| Slot | Time (IST) | Equivalent (EST) | Content Focus | Min Cooldown Since Last IG Post |
|---|---|---|---|---|
| **Morning India Peak** | `11:45 AM IST` | `1:15 AM EST` | Regional creator highlights / Hinglish hooks | `>= 6 hours` |
| **Night USA & Europe Peak** | `10:15 PM IST` | `11:45 AM EST` | Clean 4K global gameplay + English captions | `>= 6 hours` |

- Maximum **2 Reels/day** via automation; enforce same-day slot deduplication.
- Never run Instagram automation if any safety indicator triggers (wait `24–48h` cooldown and verify manually in Chrome).

## Step-by-Step Workflow

1. **Pre-flight Safety Check (`_check_page_safety`):**
   Checks URL + visible text against `IG_SUSPENSION_INDICATORS`, `/accounts/suspended/`, and `/accounts/login/`. Immediately raises `IGSafetyError` on suspension/action-block banners.
2. **Create Dialog & Video Upload:**
   Clicks `IGSelectors.NEW_POST`, attaches vertical MP4 (`9:16`, `<= 60s`), dismisses the `"Video posts are now shared as reels"` `OK` modal if shown, and advances past Crop (`Next`) -> Edit (`Next`).
3. **Lexical Caption Insertion (`_insert_caption_lexical`):**
   Instagram Web uses Meta's **Lexical editor**, which ignores Playwright `.fill()` or raw `.textContent` assignments (`caption_len=0` silent bug on publish). The script dispatches a synthetic `ClipboardEvent("paste")` and verifies live DOM readback length (`>= min(20, len(caption))`), falling back to line-by-line keyboard typing only if readback fails.
4. **Share & Poll Confirmation:**
   Clicks `Share`, polls up to `IG_POST_CONFIRM_MAX_POLLS × IG_POST_CONFIRM_POLL_MS` (`20 × 3s = 60s`) for confirmation or modal close.

## Standalone Test Command

```bash
python scripts/ig_reels_publisher.py \
  --video "C:/path/to/reel.mp4" \
  --caption "Crazy Vice City escape! #GTA6 #Reels"
```
