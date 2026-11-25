"""
Portable YouTube Studio Playwright CDP Upload Engine
----------------------------------------------------
Automates end-to-end Shorts publishing through Chrome CDP with full Pro metadata:
Title, Description, Not Made for Kids, Playlist, Altered Content, Gaming Category,
Official Game Title, US English Language, Tags, and post-publish Owner CTA Comment.
"""

import os
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config
from yt_channel_manager import (
    _is_google_auth_gate,
    apply_full_video_metadata,
    is_cdp_available,
    load_channel_state,
    post_and_pin_comment,
)


async def check_youtube_session_health(cdp_url: str | None = None) -> dict:
    cfg = load_config()
    cdp = cdp_url or cfg["cdp_url"]
    health = {
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
            browser = await p.chromium.connect_over_cdp(cdp, timeout=30000)
            if not browser.contexts:
                health["message"] = "Chrome has no active browser context."
                return health
            ctx = browser.contexts[0]
            pg = await ctx.new_page()
            try:
                await pg.bring_to_front()
                target_cid = health["channel_id"]
                studio_url = f"https://studio.youtube.com/channel/{target_cid}" if target_cid else "https://studio.youtube.com/"
                await pg.goto(studio_url, wait_until="domcontentloaded", timeout=35000)
                await pg.wait_for_timeout(4500)

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
    except Exception as e:
        health["message"] = f"Studio session error: {e}"
        return health


async def _upload_short_on_page(
    pg,
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
) -> dict:
    out = {"success": False, "video_url": None, "video_id": None, "message": ""}
    await pg.bring_to_front()
    if not target_cid or f"/channel/{target_cid}" not in pg.url:
        await pg.goto(studio_home, wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(4500)
    else:
        await pg.wait_for_timeout(1500)

    body_text = await pg.locator("body").inner_text()
    if _is_google_auth_gate(pg.url, body_text):
        out["message"] = "Google auth verification required in Chrome."
        return out

    create_btn = pg.locator("#create-icon, ytcp-button#create-icon, button[aria-label='Create']").first
    await create_btn.wait_for(state="visible", timeout=15000)
    await create_btn.click()
    await pg.wait_for_timeout(1200)

    upload_item = pg.locator("#text-item-0, tp-yt-paper-item:has-text('Upload videos')").first
    await upload_item.wait_for(state="visible", timeout=10000)
    await upload_item.click()
    await pg.wait_for_timeout(2000)

    await pg.locator("input[type='file']").first.set_input_files(video_path)
    print(f"[YT-UPLOADER] Attached {os.path.basename(video_path)}; filling Studio details...", flush=True)
    await pg.wait_for_timeout(5000)

    title_box = pg.locator("#title-textarea #textbox, ytcp-social-suggestions-textbox[id='title-textarea'] div#textbox").first
    await title_box.wait_for(state="visible", timeout=25000)
    await title_box.click()
    await pg.keyboard.press("Control+A")
    await pg.keyboard.press("Backspace")
    await pg.keyboard.insert_text(title[:100])
    await pg.wait_for_timeout(600)

    desc_box = pg.locator("#description-textarea #textbox, ytcp-social-suggestions-textbox[id='description-textarea'] div#textbox").first
    if await desc_box.count() > 0:
        await desc_box.click()
        await pg.keyboard.press("Control+A")
        await pg.keyboard.press("Backspace")
        await pg.keyboard.insert_text(description[:4900])
        await pg.wait_for_timeout(600)

    not_kids = pg.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
    if await not_kids.count() > 0:
        await not_kids.scroll_into_view_if_needed()
        await not_kids.click()
        await pg.wait_for_timeout(500)

    out["metadata_applied"] = await apply_full_video_metadata(
        pg,
        tags=tags,
        playlist_name=playlist_name,
        game_title=game_title,
        altered_content=altered_content,
        scope_selector="ytcp-uploads-dialog",
    )

    vid_id = None
    try:
        link_el = pg.locator("a[href*='youtu.be/'], a[href*='youtube.com/shorts/']").first
        if await link_el.count() > 0:
            href = await link_el.get_attribute("href") or ""
            m = re.search(r"(?:youtu\.be/|/shorts/)([\w-]+)", href)
            if m:
                vid_id = m.group(1)
    except Exception:
        pass

    for step_name in ["Details -> Elements", "Elements -> Checks", "Checks -> Visibility"]:
        next_btn = pg.locator("#next-button").first
        await next_btn.wait_for(state="visible", timeout=10000)
        await next_btn.click()
        print(f"[YT-UPLOADER] Next ({step_name})", flush=True)
        await pg.wait_for_timeout(1800)

    vis_name = visibility.upper()
    if vis_name in {"PUBLIC", "UNLISTED", "PRIVATE"}:
        vis_radio = pg.locator(f"tp-yt-paper-radio-button[name='{vis_name}']").first
        await vis_radio.wait_for(state="visible", timeout=10000)
        await vis_radio.click()
        await pg.wait_for_timeout(800)

    done_btn = pg.locator("#done-button").first
    await done_btn.wait_for(state="visible", timeout=10000)
    await done_btn.click()
    print("[YT-UPLOADER] Publish clicked! Waiting for confirmation...", flush=True)

    for _ in range(30):
        await pg.wait_for_timeout(2000)
        try:
            share_dlg = pg.locator("ytcp-video-share-dialog, ytcp-uploads-still-processing-dialog, tp-yt-paper-dialog").last
            if await share_dlg.count() > 0 and await share_dlg.is_visible():
                dlg_text = await share_dlg.inner_text()
                if not vid_id:
                    m = re.search(r"(?:youtu\.be/|/shorts/)([\w-]+)", dlg_text)
                    if m:
                        vid_id = m.group(1)
                if any(k in dlg_text.lower() for k in ["video published", "processing will begin", "video link", "share a link", "checks complete"]):
                    out["success"] = True
                    close_dlg = share_dlg.locator("#close-button, ytcp-button:has-text('Close'), button:has-text('Close')").last
                    if await close_dlg.count() > 0 and await close_dlg.is_visible():
                        await close_dlg.click()
                    break
            elif await pg.locator("ytcp-uploads-dialog").count() == 0 and vid_id:
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
) -> dict:
    cfg = load_config()
    cdp = cfg["cdp_url"]
    if not os.path.exists(video_path):
        return {"success": False, "video_url": None, "video_id": None, "message": f"Video file missing: {video_path}"}
    if not is_cdp_available(cdp):
        return {"success": False, "video_url": None, "video_id": None, "message": "Chrome CDP offline."}

    target_cid = channel_id or load_channel_state().get("channel_id")
    studio_home = f"https://studio.youtube.com/channel/{target_cid}" if target_cid else "https://studio.youtube.com/"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp, timeout=30000)
            ctx = browser.contexts[0]
            pg = await ctx.new_page()
            try:
                return await _upload_short_on_page(
                    pg,
                    video_path,
                    title,
                    description,
                    tags,
                    studio_home,
                    target_cid,
                    visibility,
                    playlist_name=playlist_name,
                    game_title=game_title,
                    altered_content=altered_content,
                    pinned_comment=pinned_comment,
                )
            finally:
                try:
                    await pg.close()
                except Exception:
                    pass
    except Exception as e:
        return {"success": False, "video_url": None, "video_id": None, "message": f"Studio upload error: {e}"}
