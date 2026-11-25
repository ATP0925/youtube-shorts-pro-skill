"""
Parameterized Instagram Reels Playwright CDP Publisher
------------------------------------------------------
Uses Meta Lexical-safe ClipboardEvent pasting, caption readback verification,
and safety circuit-breakers (never bypasses checkpoints/suspensions/2FA).
"""

import os
import re
import urllib.request
from playwright.async_api import async_playwright

from config_loader import load_config

SUSPENSION_INDICATORS = (
    "suspended your account",
    "account suspended",
    "we suspended",
    "help us confirm that it's you",
    "action blocked",
    "your account has been disabled",
    "we restrict certain activity",
    "confirm your info",
)


def is_cdp_available(cdp_url: str = "http://localhost:9222", timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(f"{cdp_url}/json/version")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _select_instagram_page(context, profile_url: str):
    ig_pages = [pg for pg in context.pages if "instagram.com" in pg.url.lower()]
    slug = profile_url.rstrip("/").split("/")[-1].lower()
    if slug:
        matched = [
            pg for pg in ig_pages
            if slug in pg.url.lower() and "/accounts/suspended" not in pg.url.lower() and "/accounts/login" not in pg.url.lower()
        ]
        if matched:
            return matched[0], True
    healthy = [pg for pg in ig_pages if "/accounts/suspended" not in pg.url.lower() and "/accounts/login" not in pg.url.lower()]
    if healthy:
        return healthy[0], True
    if ig_pages:
        return ig_pages[0], True
    return None, False


async def _check_page_safety(page) -> tuple[bool, dict]:
    curr_url = page.url.lower()
    visible_text = ""
    try:
        visible_text = (await page.locator("body").inner_text()).lower()
    except Exception:
        pass
    for ind in SUSPENSION_INDICATORS:
        if ind in curr_url or ind in visible_text:
            return False, {"suspended": True, "challenge_detected": True, "logged_in": False, "message": f"Safety trigger ('{ind}') detected."}
    if "/accounts/login" in curr_url or "/accounts/suspended" in curr_url:
        return False, {"suspended": "/accounts/suspended" in curr_url, "challenge_detected": False, "logged_in": False, "message": "Instagram session logged out or suspended."}
    return True, {"suspended": False, "challenge_detected": False, "logged_in": True, "message": "Instagram session healthy."}


async def _insert_caption_lexical(page, dialog_root, caption: str) -> bool:
    """Populate Meta's Lexical caption editor via synthetic ClipboardEvent paste + readback check."""
    caption_box = dialog_root.locator("div[aria-label*='caption' i], div[role='textbox'], div[contenteditable='true']").first
    await caption_box.wait_for(state="visible", timeout=15000)
    await caption_box.click()
    await page.wait_for_timeout(400)

    await page.evaluate(
        """(text) => {
            const dt = new DataTransfer();
            dt.setData('text/plain', text);
            const evt = new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true });
            document.activeElement.dispatchEvent(evt);
        }""",
        caption,
    )
    await page.wait_for_timeout(900)
    if len((await caption_box.inner_text()).strip()) >= min(20, len(caption.strip())):
        return True

    # Fallback: line-by-line keyboard typing
    await caption_box.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Backspace")
    lines = caption.split("\n")
    for idx, line in enumerate(lines):
        if line:
            await page.keyboard.type(line, delay=12)
        if idx < len(lines) - 1:
            await page.keyboard.press("Enter")
    await page.wait_for_timeout(900)
    return len((await caption_box.inner_text()).strip()) >= min(20, len(caption.strip()))


async def publish_reel(video_path: str, caption: str, profile_url: str | None = None, cdp_url: str | None = None) -> bool:
    """Upload a vertical MP4 Reel to Instagram via active Chrome CDP session."""
    cfg = load_config()
    cdp = cdp_url or cfg["cdp_url"]
    target_url = profile_url or cfg.get("ig_profile_url", "https://www.instagram.com/")

    if not os.path.exists(video_path):
        print(f"[IG] Video missing: {video_path}")
        return False
    if not is_cdp_available(cdp):
        print(f"[IG] CDP unavailable at {cdp}")
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp, timeout=30000)
            if not browser.contexts:
                return False
            ctx = browser.contexts[0]
            page, _ = _select_instagram_page(ctx, target_url)
            created_tab = False
            if page is None:
                page = await ctx.new_page()
                created_tab = True
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
                is_safe, info = await _check_page_safety(page)
                if not is_safe:
                    print(f"[IG CIRCUIT_BREAKER] {info['message']}")
                    return False

                post_btn = page.locator("svg[aria-label='New post'], svg[aria-label='Post'], svg[aria-label='Create']").first
                if await post_btn.count() == 0:
                    print("[IG] Create button not found.")
                    return False
                await post_btn.click()
                await page.wait_for_timeout(2000)

                dlg = page.locator("div[role='dialog']").last
                inp = page.locator("input[type='file'][accept*='video/mp4']").first
                if await inp.count() == 0:
                    inp = page.locator("input[type='file']").last
                await inp.set_input_files(video_path)
                await page.wait_for_timeout(5000)

                ok_btn = page.locator("button:has-text('OK'), div[role='button']:has-text('OK')").first
                if await ok_btn.count() > 0 and await ok_btn.is_visible():
                    await ok_btn.click()
                    await page.wait_for_timeout(1000)

                for _ in range(2):
                    nxt = dlg.locator("div[role='button']:has-text('Next'), button:has-text('Next')").first
                    if await nxt.count() > 0:
                        await nxt.click(force=True)
                        await page.wait_for_timeout(2500)

                if not await _insert_caption_lexical(page, dlg, caption):
                    print("[IG] Caption readback verification failed; aborting post.")
                    return False

                share_btn = dlg.locator("div[role='button'], button").filter(has_text=re.compile(r"^Share$")).last
                if await share_btn.count() == 0:
                    return False
                await share_btn.click(force=True)

                for _ in range(20):
                    await page.wait_for_timeout(3000)
                    cnt = await page.locator("div[role='dialog']").count()
                    txt = (await page.locator("div[role='dialog']").first.inner_text()).lower() if cnt > 0 else ""
                    if "shared" in txt or cnt == 0:
                        print("[IG] Reel shared cleanly!")
                        return True
                return False
            finally:
                if created_tab:
                    await page.close()
    except Exception as exc:
        print(f"[IG] Unexpected upload error: {exc}")
        return False
