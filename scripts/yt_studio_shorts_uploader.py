"""
Portable YouTube Studio Playwright CDP Upload Engine.

Automates end-to-end Shorts publishing through Chrome CDP with full Pro metadata:
Title, Description, Not Made for Kids, Playlist, Altered Content, Gaming Category,
Official Game Title, US English Language, Tags, and post-publish Owner CTA Comment.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import is_cdp_available, load_config, resolve_cdp_url
from constants import (
    CDP_CONNECT_TIMEOUT_MS,
    CREATE_BUTTON_TIMEOUT_MS,
    DROPDOWN_SETTLE_MS,
    LONG_SETTLE_MS,
    MAX_STUDIO_DESC_LENGTH,
    MAX_STUDIO_TITLE_LENGTH,
    MEDIUM_SETTLE_MS,
    PAGE_LOAD_TIMEOUT_MS,
    SETTINGS_OPEN_SETTLE_MS,
    STEP_NEXT_SETTLE_MS,
    STUDIO_SETTLE_MS,
    TITLE_BOX_TIMEOUT_MS,
    UPLOAD_ATTACH_SETTLE_MS,
    UPLOAD_CONFIRM_MAX_POLLS,
    UPLOAD_CONFIRM_POLL_MS,
    UPLOAD_ITEM_TIMEOUT_MS,
)
from constants import (
    StudioSelectors as S,
)
from exceptions import AuthGateError, UploadError
from logger import get_logger
from yt_channel_manager import (
    _is_google_auth_gate,
    apply_full_video_metadata,
    load_channel_state,
    post_and_pin_comment,
)

log = get_logger(__name__)

__all__ = ["check_youtube_session_health", "upload_youtube_short"]


async def check_youtube_session_health(cdp_url: str | None = None) -> dict[str, Any]:
    """Verify that YouTube Studio is accessible via CDP.

    Returns:
        Health report dict with healthy, cdp_available, requires_manual_auth, etc.
    """
    cfg = load_config()
    cdp = resolve_cdp_url(cdp_url or cfg["cdp_url"])
    health: dict[str, Any] = {
        "healthy": False,
        "cdp_available": False,
        "requires_manual_auth": False,
        "current_url": None,
        "channel_id": load_channel_state().get("channel_id"),
        "message": "",
    }

    if not is_cdp_available(cdp):
        health["message"] = f"CDP port ({cdp}) is offline / not responding."
        return health

    health["cdp_available"] = True
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
            if not browser.contexts:
                health["message"] = "Chrome has no active browser context."
                return health
            pg = await browser.contexts[0].new_page()
            try:
                await pg.bring_to_front()
                target_cid = health["channel_id"]
                studio_url = f"https://studio.youtube.com/channel/{target_cid}" if target_cid else "https://studio.youtube.com/"
                await pg.goto(studio_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)
                await pg.wait_for_timeout(STUDIO_SETTLE_MS)

                curr_url = pg.url
                health["current_url"] = curr_url
                body_text = await pg.locator("body").inner_text()

                if _is_google_auth_gate(curr_url, body_text):
                    health["requires_manual_auth"] = True
                    health["message"] = "Google requires manual verification in Chrome."
                    return health

                m = re.search(r"/channel/(UC[\w-]+)", curr_url)
                if m:
                    health["channel_id"] = m.group(1)

                if "studio.youtube.com" in curr_url.lower():
                    health["healthy"] = True
                    health["message"] = f"YouTube Studio active ({health['channel_id']})."
                else:
                    health["message"] = f"Unexpected Studio redirect: {curr_url}"
                return health
            finally:
                await pg.close()
    except Exception as exc:
        health["message"] = f"Studio session error: {exc}"
        return health


async def _upload_short_on_page(
    pg: Any,
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    studio_home: str,
    target_cid: str | None,
    visibility: str,
    playlist_name: str | None = None,
    game_title: str | None = None,
    altered_content: bool = False,
    pinned_comment: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Execute the full upload flow on a Studio page.

    Raises:
        AuthGateError: Immediately if Google prompts for manual verification.
        UploadError: If Studio upload UI elements fail to respond.
    """
    out: dict[str, Any] = {"success": False, "video_url": None, "video_id": None, "message": ""}
    await pg.bring_to_front()

    if not target_cid or f"/channel/{target_cid}" not in pg.url:
        await pg.goto(studio_home, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)
        await pg.wait_for_timeout(STUDIO_SETTLE_MS)
    else:
        await pg.wait_for_timeout(LONG_SETTLE_MS)

    body_text = await pg.locator("body").inner_text()
    if _is_google_auth_gate(pg.url, body_text):
        raise AuthGateError(pg.url)

    # Open upload dialog
    try:
        create_btn = pg.locator(S.CREATE_BUTTON).first
        await create_btn.wait_for(state="visible", timeout=CREATE_BUTTON_TIMEOUT_MS)
        await create_btn.click()
        await pg.wait_for_timeout(DROPDOWN_SETTLE_MS)

        upload_item = pg.locator(S.UPLOAD_ITEM).first
        await upload_item.wait_for(state="visible", timeout=UPLOAD_ITEM_TIMEOUT_MS)
        await upload_item.click()
        await pg.wait_for_timeout(SETTINGS_OPEN_SETTLE_MS)
    except Exception as exc:
        raise UploadError(video_path, f"Could not open Studio upload dialog: {exc}") from exc

    # Attach file
    await pg.locator(S.FILE_INPUT).first.set_input_files(video_path)
    log.info("Attached %s; filling Studio details...", os.path.basename(video_path))
    await pg.wait_for_timeout(UPLOAD_ATTACH_SETTLE_MS)

    # Title
    title_box = pg.locator(S.TITLE_TEXTBOX).first
    await title_box.wait_for(state="visible", timeout=TITLE_BOX_TIMEOUT_MS)
    await title_box.click()
    await pg.keyboard.press("Control+A")
    await pg.keyboard.press("Backspace")
    await pg.keyboard.insert_text(title[:MAX_STUDIO_TITLE_LENGTH])
    await pg.wait_for_timeout(MEDIUM_SETTLE_MS)

    # Description
    desc_box = pg.locator(S.DESC_TEXTBOX).first
    if await desc_box.count() > 0:
        await desc_box.click()
        await pg.keyboard.press("Control+A")
        await pg.keyboard.press("Backspace")
        await pg.keyboard.insert_text(description[:MAX_STUDIO_DESC_LENGTH])
        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)

    # Not Made for Kids
    not_kids = pg.locator(S.NOT_MADE_FOR_KIDS).first
    if await not_kids.count() > 0:
        await not_kids.scroll_into_view_if_needed()
        await not_kids.click()
        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)

    # Full metadata
    out["metadata_applied"] = await apply_full_video_metadata(
        pg,
        tags=tags,
        playlist_name=playlist_name,
        game_title=game_title,
        altered_content=altered_content,
        scope_selector=S.UPLOADS_DIALOG,
        category=category,
    )

    # Extract video ID
    vid_id = None
    try:
        link_el = pg.locator(S.VIDEO_LINK).first
        if await link_el.count() > 0:
            href = await link_el.get_attribute("href") or ""
            m = re.search(r"(?:youtu\.be/|/shorts/)([\w-]+)", href)
            if m:
                vid_id = m.group(1)
    except Exception:
        pass

    # Navigate through dialog steps
    for step_name in ("Details → Elements", "Elements → Checks", "Checks → Visibility"):
        next_btn = pg.locator(S.NEXT_BUTTON).first
        await next_btn.wait_for(state="visible", timeout=UPLOAD_ITEM_TIMEOUT_MS)
        await next_btn.click()
        log.debug("Next (%s)", step_name)
        await pg.wait_for_timeout(STEP_NEXT_SETTLE_MS)

    # Set visibility
    vis_name = visibility.upper()
    if vis_name in {"PUBLIC", "UNLISTED", "PRIVATE"}:
        vis_radio = pg.locator(S.VISIBILITY_RADIO.format(visibility=vis_name)).first
        await vis_radio.wait_for(state="visible", timeout=UPLOAD_ITEM_TIMEOUT_MS)
        await vis_radio.click()
        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)

    # Wait for raw file byte transfer to finish before publishing/closing tab
    for poll_idx in range(UPLOAD_CONFIRM_MAX_POLLS):
        try:
            up_txt = (await pg.locator(S.UPLOADS_DIALOG).first.inner_text()).lower()
            if not re.search(r"uploading\s+\d+%", up_txt):
                break
            if poll_idx % 3 == 0:
                log.info("Waiting for Studio file upload transfer to hit 100%%...")
        except Exception:
            break
        await pg.wait_for_timeout(UPLOAD_CONFIRM_POLL_MS)

    # Publish
    done_btn = pg.locator(S.DONE_BUTTON).first
    await done_btn.wait_for(state="visible", timeout=UPLOAD_ITEM_TIMEOUT_MS)
    await done_btn.click()
    log.info("Publish clicked — waiting for confirmation...")

    # Wait for confirmation (and verify no active upload transfer remains)
    for _ in range(UPLOAD_CONFIRM_MAX_POLLS):
        await pg.wait_for_timeout(UPLOAD_CONFIRM_POLL_MS)
        try:
            share_dlg = pg.locator(S.SHARE_DIALOG).last
            if await share_dlg.count() > 0 and await share_dlg.is_visible():
                dlg_text = await share_dlg.inner_text()
                if not vid_id:
                    m = re.search(r"(?:youtu\.be/|/shorts/)([\w-]+)", dlg_text)
                    if m:
                        vid_id = m.group(1)
                low_txt = dlg_text.lower()
                if re.search(r"uploading\s+\d+%", low_txt):
                    continue
                done_keywords = (
                    "video published",
                    "processing will begin",
                    "video link",
                    "share a link",
                    "checks complete",
                )
                if any(k in low_txt for k in done_keywords):
                    out["success"] = True
                    close_dlg = share_dlg.locator(S.SHARE_CLOSE_BUTTON).last
                    if await close_dlg.count() > 0 and await close_dlg.is_visible():
                        await close_dlg.click()
                    break
            elif await pg.locator(S.UPLOADS_DIALOG).count() == 0 and vid_id:
                out["success"] = True
                break
        except Exception:
            pass

    if vid_id:
        out["video_id"] = vid_id
        out["video_url"] = f"https://youtube.com/shorts/{vid_id}"
        if out["success"] and visibility.upper() == "PUBLIC" and pinned_comment:
            out["comment"] = await post_and_pin_comment(pg, vid_id, pinned_comment)

    out["message"] = "YouTube Short uploaded and published." if out["success"] else "Upload triggered; check Studio."
    return out


async def upload_youtube_short(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    channel_id: str | None = None,
    visibility: str = "Public",
    playlist_name: str | None = None,
    game_title: str | None = None,
    altered_content: bool = False,
    pinned_comment: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Upload a YouTube Short with complete pro metadata.

    Args:
        video_path: Absolute path to the video file.
        title: Short title (≤100 chars).
        description: Short description.
        tags: List of tag strings.
        channel_id: Override channel ID (defaults to config).
        visibility: "Public", "Unlisted", or "Private".
        playlist_name: Playlist to assign.
        game_title: Official game title for autocomplete.
        altered_content: Whether content is AI-altered.
        pinned_comment: Owner CTA comment to post after publish.

    Returns:
        Result dict with success, video_url, video_id, message.

    Raises:
        AuthGateError: If Google requires manual verification in Chrome.
    """
    cfg = load_config()
    cdp = resolve_cdp_url(cfg["cdp_url"])

    if not os.path.exists(video_path):
        return {"success": False, "video_url": None, "video_id": None, "message": f"Video file missing: {video_path}"}
    if not is_cdp_available(cdp):
        return {"success": False, "video_url": None, "video_id": None, "message": "Chrome CDP offline."}

    target_cid = channel_id or load_channel_state().get("channel_id")
    studio_home = f"https://studio.youtube.com/channel/{target_cid}" if target_cid else "https://studio.youtube.com/"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
            if not browser.contexts:
                return {
                    "success": False,
                    "video_url": None,
                    "video_id": None,
                    "message": "Chrome has no active context.",
                }
            pg = await browser.contexts[0].new_page()
            try:
                return await _upload_short_on_page(
                    pg, video_path, title, description, tags,
                    studio_home, target_cid, visibility,
                    playlist_name=playlist_name,
                    game_title=game_title,
                    altered_content=altered_content,
                    pinned_comment=pinned_comment,
                    category=category,
                )
            finally:
                try:
                    await pg.close()
                except Exception:
                    pass
    except AuthGateError:
        raise
    except UploadError as exc:
        return {"success": False, "video_url": None, "video_id": None, "message": str(exc)}
    except Exception as exc:
        return {"success": False, "video_url": None, "video_id": None, "message": f"Studio upload error: {exc}"}
