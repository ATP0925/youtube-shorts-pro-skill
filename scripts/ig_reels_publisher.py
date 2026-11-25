"""
Parameterized Instagram Reels Playwright CDP Publisher.

Uses Meta Lexical-safe ClipboardEvent pasting, caption readback verification,
and safety circuit-breakers (never bypasses checkpoints/suspensions/2FA).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import is_cdp_available, load_config
from constants import (
    CDP_CONNECT_TIMEOUT_MS,
    DROPDOWN_SETTLE_MS,
    IG_CAPTION_MIN_LENGTH,
    IG_NEXT_STEP_SETTLE_MS,
    IG_POST_CONFIRM_MAX_POLLS,
    IG_POST_CONFIRM_POLL_MS,
    IG_SUSPENSION_INDICATORS,
    LONG_SETTLE_MS,
    MEDIUM_SETTLE_MS,
    PAGE_LOAD_TIMEOUT_MS,
    STUDIO_SETTLE_MS,
    UPLOAD_ATTACH_SETTLE_MS,
    IGSelectors,
)
from exceptions import CDPConnectionError, IGSafetyError
from logger import get_logger

log = get_logger(__name__)

__all__ = ["publish_reel"]


def _select_instagram_page(context: Any, profile_url: str) -> tuple[Any, bool]:
    """Find an existing healthy Instagram tab or return ``(None, False)``."""
    ig_pages = [pg for pg in context.pages if "instagram.com" in pg.url.lower()]
    slug = profile_url.rstrip("/").split("/")[-1].lower()
    if slug:
        matched = [
            pg for pg in ig_pages
            if slug in pg.url.lower()
            and "/accounts/suspended" not in pg.url.lower()
            and "/accounts/login" not in pg.url.lower()
        ]
        if matched:
            return matched[0], True
    healthy = [
        pg for pg in ig_pages
        if "/accounts/suspended" not in pg.url.lower()
        and "/accounts/login" not in pg.url.lower()
    ]
    if healthy:
        return healthy[0], True
    if ig_pages:
        return ig_pages[0], True
    return None, False


async def _check_page_safety(page: Any) -> tuple[bool, dict[str, Any]]:
    """Pre-flight safety check for suspension, blocks, or login requirement.

    Raises:
        IGSafetyError: If a suspension or safety indicator is detected.
    """
    curr_url = page.url.lower()
    visible_text = ""
    try:
        visible_text = (await page.locator("body").inner_text()).lower()
    except Exception:
        pass

    for ind in IG_SUSPENSION_INDICATORS:
        if ind in curr_url or ind in visible_text:
            raise IGSafetyError(ind, page.url)

    if "/accounts/login" in curr_url or "/accounts/suspended" in curr_url:
        is_suspended = "/accounts/suspended" in curr_url
        if is_suspended:
            raise IGSafetyError("account suspended", page.url)
        return False, {
            "suspended": False,
            "challenge_detected": False,
            "logged_in": False,
            "message": "Instagram session logged out.",
        }

    return True, {
        "suspended": False,
        "challenge_detected": False,
        "logged_in": True,
        "message": "Instagram session healthy.",
    }


async def _insert_caption_lexical(page: Any, dialog_root: Any, caption: str) -> bool:
    """Populate Meta's Lexical caption editor via synthetic ClipboardEvent paste.

    Falls back to line-by-line keyboard typing if paste doesn't take.
    """
    caption_box = dialog_root.locator(IGSelectors.CAPTION_BOX).first
    await caption_box.wait_for(state="visible", timeout=LONG_SETTLE_MS * 10)
    await caption_box.click()
    await page.wait_for_timeout(MEDIUM_SETTLE_MS)

    await page.evaluate(
        """(text) => {
            const dt = new DataTransfer();
            dt.setData('text/plain', text);
            const evt = new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true });
            document.activeElement.dispatchEvent(evt);
        }""",
        caption,
    )
    await page.wait_for_timeout(DROPDOWN_SETTLE_MS)

    actual_len = len((await caption_box.inner_text()).strip())
    threshold = min(IG_CAPTION_MIN_LENGTH, len(caption.strip()))
    if actual_len >= threshold:
        log.debug("Caption inserted via ClipboardEvent paste (%d chars)", actual_len)
        return True

    log.debug("ClipboardEvent paste insufficient (%d chars), falling back to keyboard", actual_len)
    await caption_box.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Backspace")
    lines = caption.split("\n")
    for idx, line in enumerate(lines):
        if line:
            await page.keyboard.type(line, delay=12)
        if idx < len(lines) - 1:
            await page.keyboard.press("Enter")
    await page.wait_for_timeout(DROPDOWN_SETTLE_MS)

    final_len = len((await caption_box.inner_text()).strip())
    return final_len >= threshold


async def publish_reel(
    video_path: str,
    caption: str,
    profile_url: str | None = None,
    cdp_url: str | None = None,
) -> bool:
    """Upload a vertical MP4 Reel to Instagram via active Chrome CDP session.

    Args:
        video_path: Absolute path to the video file.
        caption: Reel caption text.
        profile_url: Target Instagram profile URL.
        cdp_url: Chrome CDP endpoint URL.

    Returns:
        ``True`` if the reel was shared successfully.

    Raises:
        CDPConnectionError: If CDP is unreachable.
        IGSafetyError: If suspension/block indicators are detected.
    """
    cfg = load_config()
    cdp = cdp_url or cfg["cdp_url"]
    target_url = profile_url or cfg.get("ig_profile_url", "https://www.instagram.com/")

    if not os.path.exists(video_path):
        log.error("Video missing: %s", video_path)
        return False
    if not is_cdp_available(cdp):
        raise CDPConnectionError(cdp, "Instagram publisher cannot connect")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
            if not browser.contexts:
                log.error("Chrome has no active browser context")
                return False
            ctx = browser.contexts[0]
            page, _ = _select_instagram_page(ctx, target_url)
            created_tab = False
            if page is None:
                page = await ctx.new_page()
                created_tab = True
            try:
                # Retry once on transient page load stall
                for attempt in range(2):
                    try:
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)
                        break
                    except Exception:
                        if attempt == 1:
                            raise
                        await page.wait_for_timeout(LONG_SETTLE_MS)

                await page.wait_for_timeout(STUDIO_SETTLE_MS)

                is_safe, info = await _check_page_safety(page)
                if not is_safe:
                    log.warning("IG session not safe: %s", info["message"])
                    return False

                post_btn = page.locator(IGSelectors.NEW_POST).first
                if await post_btn.count() == 0:
                    log.error("Create button not found on Instagram")
                    return False
                await post_btn.click()
                await page.wait_for_timeout(IG_NEXT_STEP_SETTLE_MS)

                dlg = page.locator(IGSelectors.DIALOG).last
                inp = page.locator(IGSelectors.FILE_INPUT_VIDEO).first
                if await inp.count() == 0:
                    inp = page.locator(IGSelectors.FILE_INPUT_ANY).last
                await inp.set_input_files(video_path)
                log.info("Video attached to Instagram upload dialog")
                await page.wait_for_timeout(UPLOAD_ATTACH_SETTLE_MS)

                ok_btn = page.locator(IGSelectors.OK_BUTTON).first
                if await ok_btn.count() > 0 and await ok_btn.is_visible():
                    await ok_btn.click()
                    await page.wait_for_timeout(DROPDOWN_SETTLE_MS)

                for _ in range(2):
                    nxt = dlg.locator(IGSelectors.NEXT_BUTTON).first
                    if await nxt.count() > 0:
                        await nxt.click(force=True)
                        await page.wait_for_timeout(IG_NEXT_STEP_SETTLE_MS)

                if not await _insert_caption_lexical(page, dlg, caption):
                    log.error("Caption readback verification failed; aborting post")
                    return False

                share_btn = dlg.locator(IGSelectors.SHARE_BUTTON).filter(has_text=re.compile(r"^Share$")).last
                if await share_btn.count() == 0:
                    log.error("Share button not found")
                    return False
                await share_btn.click(force=True)
                log.info("Share clicked — waiting for confirmation...")

                for _ in range(IG_POST_CONFIRM_MAX_POLLS):
                    await page.wait_for_timeout(IG_POST_CONFIRM_POLL_MS)
                    cnt = await page.locator(IGSelectors.DIALOG).count()
                    txt = ""
                    if cnt > 0:
                        txt = (await page.locator(IGSelectors.DIALOG).first.inner_text()).lower()
                    if "shared" in txt or cnt == 0:
                        log.info("Reel shared successfully!")
                        return True

                log.warning("Share confirmation not detected after %d polls", IG_POST_CONFIRM_MAX_POLLS)
                return False
            finally:
                if created_tab:
                    try:
                        await page.close()
                    except Exception:
                        pass
    except (IGSafetyError, CDPConnectionError):
        raise
    except Exception as exc:
        log.error("Unexpected IG upload error: %s", exc)
        return False


def main() -> None:
    """Standalone CLI for publishing a single Reel via Instagram Web CDP."""
    parser = argparse.ArgumentParser(description="Publish an Instagram Reel via Chrome CDP")
    parser.add_argument("--video", required=True, help="Path to vertical .mp4 file")
    parser.add_argument("--caption", required=True, help="Reel caption text")
    parser.add_argument("--profile-url", help="Override target Instagram profile URL")
    args = parser.parse_args()

    ok = asyncio.run(publish_reel(args.video, args.caption, profile_url=args.profile_url))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
