# Optional Instagram Reels Dual-Slot Cross-Platform Guide

For regional/Hindi audiences or companion traffic back to YouTube, run Instagram Reels on a dedicated schedule using safe browser CDP practices:

1. **Dual Target Slots (No Overlap & Anti-Spam Cooldown):**
   - **Morning India Peak (`11:45 AM IST`):** Regional creator highlights / Hinglish hooks.
   - **Night USA & Europe Peak (`10:15 PM IST` / `22:15`):** Clean 4K global gameplay + English captions.
   - Enforce `>= 4-6h` cooldown between IG uploads plus same-day slot dedup.

2. **Lexical Caption Editor Safety (`ig_reels_publisher.py`):**
   - Instagram Web uses Meta's **Lexical editor**, which ignores `.fill()` or raw JS text assignment on submit (`caption_len=0` silent post failure).
   - Populate captions via synthetic `ClipboardEvent("paste")` with verified DOM text readback before clicking **Share**.

3. **Safety Circuit-Breaker:**
   - Pre-flight check `/accounts/suspended/`, `/accounts/login/`, `checkpoint`, or `challenge_detected`. Halt immediately and never attempt automated CAPTCHA/checkpoint bypass.
