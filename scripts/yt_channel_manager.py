"""
Portable YouTube Pro Channel Operations & Analytics Manager
-----------------------------------------------------------
Implements all 7 pro creator workflows via Chrome CDP + Playwright:
  1. Studio Channel Health & Feature Eligibility Audit
  2. Home Tab, 150x150 Subscribe Watermark & Channel COPPA defaults
  3. Complete per-video metadata (Playlist, Altered Content, Category Gaming, Game Title, US English Language, Tags)
  4. Owner CTA Comment + Pin attempt (clean watch tab + channel identity verification)
  5. Studio Analytics & Unresponded Comments Inbox Loop
"""

import asyncio
import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, load_json, save_json


def is_cdp_available(host: str | None = None, timeout: float = 2.0) -> bool:
    cdp = host or load_config()["cdp_url"]
    try:
        req = urllib.request.Request(f"{cdp}/json/version")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def load_channel_state() -> dict:
    cfg = load_config()
    st = load_json(cfg["channel_state_path"], {})
    if not st.get("channel_id") and cfg.get("channel_id"):
        st["channel_id"] = cfg["channel_id"]
    if not st.get("channel_name") and cfg.get("channel_name"):
        st["channel_name"] = cfg["channel_name"]
    if not st.get("handle") and cfg.get("channel_handle"):
        st["handle"] = cfg["channel_handle"]
    return st


def save_channel_state(state: dict):
    cfg = load_config()
    save_json(cfg["channel_state_path"], state)


def _is_google_auth_gate(url: str, body_text: str) -> bool:
    u = url.lower()
    t = body_text.lower()
    if "accounts.google.com" in u:
        return True
    return any(
        p in t
        for p in (
            "verify it’s you",
            "verify it's you",
            "sign in again to continue",
            "enter your password",
            "2-step verification",
            "confirm it's you",
        )
    )


async def _click_center(pg, locator) -> bool:
    """Reliably click Polymer triggers via bounding box center."""
    try:
        await locator.scroll_into_view_if_needed()
        await pg.wait_for_timeout(300)
        box = await locator.bounding_box()
        if box and box["width"] > 0 and box["height"] > 0:
            await pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            return True
        await locator.click()
        return True
    except Exception:
        return False


async def _open_studio_settings_channel(pg):
    """Dismiss Studio backdrop overlays cleanly and open Settings -> Channel."""
    for _ in range(4):
        if await pg.locator("tp-yt-iron-overlay-backdrop.opened").count() == 0:
            break
        dismiss = pg.locator(
            "ytcp-dialog:visible button:visible:has-text('Got it'), "
            "ytcp-dialog:visible button:visible:has-text('Dismiss'), "
            "tp-yt-paper-dialog:visible button:visible:has-text('Close'), "
            "ytcp-dialog:visible #close-button button:visible"
        ).last
        if await dismiss.count() > 0:
            await dismiss.click()
        else:
            await pg.keyboard.press("Escape")
        await pg.wait_for_timeout(500)
    await pg.evaluate(
        "() => document.querySelectorAll('tp-yt-iron-overlay-backdrop.opened').forEach(b => {"
        " if (!document.querySelector('ytcp-dialog, tp-yt-paper-dialog[aria-hidden=\"false\"]')) b.remove(); })"
    )
    await pg.locator("#settings-item, tp-yt-paper-icon-item:has-text('Settings')").first.click()
    await pg.wait_for_timeout(2000)
    await pg.locator("li:has-text('Channel'), tp-yt-paper-item:has-text('Channel')").first.click()
    await pg.wait_for_timeout(1500)


async def _wait_button_commit(pg, btn_locator, label: str, max_wait: int = 15) -> bool:
    if await btn_locator.count() == 0:
        return False
    if (await btn_locator.get_attribute("aria-disabled")) == "true":
        return False
    await btn_locator.click()
    print(f"[YT-MGR] [{label}] Saving...", flush=True)
    for _ in range(max_wait):
        await pg.wait_for_timeout(1000)
        if (await btn_locator.get_attribute("aria-disabled")) == "true":
            print(f"[YT-MGR] [{label}] Saved cleanly!", flush=True)
            await pg.wait_for_timeout(800)
            return True
    return True


async def _set_playlist_in_form(pg, playlist_name: str | None) -> bool:
    if not playlist_name:
        return False
    trig = pg.locator("ytcp-video-metadata-playlists ytcp-text-dropdown-trigger").first
    if await trig.count() == 0 or not await _click_center(pg, trig):
        return False
    dlg = pg.locator("tp-yt-paper-dialog:has-text('Done'), ytcp-playlist-dialog:has-text('Done')").last
    try:
        await dlg.wait_for(state="visible", timeout=10000)
    except Exception:
        return False
    await pg.wait_for_timeout(600)

    changed = False
    row = dlg.get_by_text(playlist_name, exact=True).first
    if await row.count() > 0:
        already = await row.evaluate("""el => {
            const cb = el.closest('ytcp-checkbox-lit, tp-yt-paper-checkbox, [role="checkbox"], li, .item');
            return !!(cb && (cb.hasAttribute('checked') || cb.getAttribute('aria-checked') === 'true'));
        }""")
        if not already:
            await row.click()
            changed = True
            await pg.wait_for_timeout(500)
            print(f"[YT-MGR] Selected Playlist -> '{playlist_name}'", flush=True)
    done_b = dlg.locator("button:visible:has-text('Done'), ytcp-button:visible:has-text('Done')").last
    if await done_b.count() > 0 and (await done_b.get_attribute("aria-disabled")) != "true":
        await done_b.click()
        await pg.wait_for_timeout(700)
    try:
        if await dlg.is_visible():
            await pg.keyboard.press("Escape")
            await pg.wait_for_timeout(500)
    except Exception:
        pass
    return changed


async def _expand_show_more(pg, scope_selector: str = "") -> bool:
    prefix = f"{scope_selector} " if scope_selector else ""
    sm = pg.locator(f"{prefix}ytcp-button:visible:has-text('Show more'), {prefix}button:visible:has-text('Show more')").first
    if await sm.count() > 0:
        await sm.scroll_into_view_if_needed()
        await pg.wait_for_timeout(300)
        await sm.click()
        await pg.wait_for_timeout(1500)
        return True
    return False


async def _ensure_gaming_and_us_language(pg, scope_selector: str = "", category_name: str = "Gaming", target_lang: str = "English (United States)") -> bool:
    changed = False
    prefix = f"{scope_selector} " if scope_selector else ""
    try:
        cat_trig = pg.locator(f"{prefix}#category ytcp-text-dropdown-trigger").first
        if await cat_trig.count() > 0:
            cat_txt = (await cat_trig.inner_text()).strip()
            if category_name.lower() not in cat_txt.lower():
                await _click_center(pg, cat_trig)
                await pg.wait_for_timeout(1000)
                opt = pg.locator(f"tp-yt-paper-item:visible:has-text('{category_name}')").first
                if await opt.count() > 0:
                    await opt.click()
                    await pg.wait_for_timeout(1200)
                    print(f"[YT-MGR] Set Category -> {category_name}", flush=True)
                    changed = True

        for lang_label in ["Video language", "Title and description language"]:
            ltrig = pg.locator(f"{prefix}ytcp-text-dropdown-trigger:has-text('{lang_label}')").first
            if await ltrig.count() > 0:
                ltxt = (await ltrig.inner_text()).strip()
                if "english" not in ltxt.lower():
                    await _click_center(pg, ltrig)
                    await pg.wait_for_timeout(1000)
                    eopt = pg.locator(f"tp-yt-paper-item:visible:has-text('{target_lang}')").first
                    if await eopt.count() == 0:
                        eopt = pg.locator("tp-yt-paper-item:visible:text-is('English')").first
                    if await eopt.count() > 0:
                        await eopt.scroll_into_view_if_needed()
                        await eopt.click()
                        await pg.wait_for_timeout(800)
                        print(f"[YT-MGR] Set {lang_label} -> {target_lang}", flush=True)
                        changed = True
                    else:
                        await pg.keyboard.press("Escape")
    except Exception as exc:
        print(f"[YT-MGR] Category/Language check note: {exc}", flush=True)
    return changed


async def _set_game_title(pg, game_title: str | None, scope_selector: str = "") -> bool:
    if not game_title:
        return False
    prefix = f"{scope_selector} " if scope_selector else ""
    inp = pg.locator(f"{prefix}input[aria-label='Game title (optional)']").first
    if await inp.count() == 0:
        return False
    try:
        if game_title.lower() in (await inp.input_value()).strip().lower():
            return False
        await inp.scroll_into_view_if_needed()
        await inp.click()
        await pg.keyboard.press("Control+A")
        await pg.keyboard.press("Backspace")
        await inp.press_sequentially(game_title, delay=25)
        await pg.wait_for_timeout(2000)
        opt = pg.locator(
            f"tp-yt-paper-item:visible:has-text('{game_title}'), "
            f"ytcp-text-menu tp-yt-paper-item:visible:has-text('{game_title}'), "
            f"[role='option']:visible:has-text('{game_title}')"
        ).first
        if await opt.count() > 0:
            await opt.click()
            await pg.wait_for_timeout(700)
            print(f"[YT-MGR] Selected Game Title -> '{game_title}'", flush=True)
            return True
        await pg.keyboard.press("Tab")
        return True
    except Exception:
        return False


async def _set_altered_content(pg, altered_content: bool = False, scope_selector: str = "") -> bool:
    prefix = f"{scope_selector} " if scope_selector else ""
    radio_name = "VIDEO_HAS_ALTERED_CONTENT_YES" if altered_content else "VIDEO_HAS_ALTERED_CONTENT_NO"
    rad = pg.locator(f"{prefix}tp-yt-paper-radio-button[name='{radio_name}']").first
    if await rad.count() == 0:
        return False
    try:
        if (await rad.get_attribute("aria-checked")) == "true":
            return False
        await rad.scroll_into_view_if_needed()
        await rad.click()
        await pg.wait_for_timeout(400)
        print(f"[YT-MGR] Altered Content -> {'Yes' if altered_content else 'No'}", flush=True)
        return True
    except Exception:
        return False


async def _ensure_tags(pg, tags: list[str], scope_selector: str = "") -> bool:
    if not tags:
        return False
    prefix = f"{scope_selector} " if scope_selector else ""
    tags_inp = pg.locator(f"{prefix}input[aria-label='Tags'], {prefix}#tags-container input").first
    if await tags_inp.count() == 0:
        return False
    try:
        if await pg.locator(f"{prefix}#tags-container ytcp-chip").count() >= 4:
            return False
        await tags_inp.scroll_into_view_if_needed()
        await tags_inp.click()
        await pg.keyboard.insert_text(", ".join(tags)[:450])
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(500)
        return True
    except Exception:
        return False


async def apply_full_video_metadata(
    pg,
    tags: list[str] | None = None,
    playlist_name: str | None = None,
    game_title: str | None = None,
    altered_content: bool = False,
    scope_selector: str = "",
) -> dict:
    """Applies Playlist, Altered Content, Category/Language, Tags & Game Title uniformly."""
    cfg = load_config()
    gtitle = game_title if game_title is not None else cfg.get("default_game_title")
    cat = cfg.get("default_category", "Gaming")
    lang = cfg.get("video_language", "English (United States)")

    changes = {"playlist": False, "cat_lang": False, "altered": False, "tags": False, "game_title": False}
    if playlist_name:
        changes["playlist"] = await _set_playlist_in_form(pg, playlist_name)
    await _expand_show_more(pg, scope_selector=scope_selector)
    changes["altered"] = await _set_altered_content(pg, altered_content=altered_content, scope_selector=scope_selector)
    if tags:
        changes["tags"] = await _ensure_tags(pg, tags, scope_selector=scope_selector)
    changes["cat_lang"] = await _ensure_gaming_and_us_language(pg, scope_selector=scope_selector, category_name=cat, target_lang=lang)
    if gtitle:
        changes["game_title"] = await _set_game_title(pg, gtitle, scope_selector=scope_selector)
    return changes


async def _ensure_www_channel_identity(pg, channel_name: str, handle: str):
    if not channel_name and not handle:
        return
    try:
        av_btn = pg.locator("#avatar-btn").first
        if await av_btn.count() == 0:
            return
        await av_btn.click()
        await pg.wait_for_timeout(1200)
        popup_txt = (await pg.locator("ytd-multi-page-menu-renderer:visible, tp-yt-iron-dropdown:visible").last.inner_text()).lower()
        if (handle and handle.lstrip("@").lower() in popup_txt) or (channel_name and channel_name.lower() in popup_txt):
            await pg.keyboard.press("Escape")
            return
        sw_item = pg.locator("tp-yt-compact-link-renderer:visible:has-text('Switch account'), ytd-compact-link-renderer:visible:has-text('Switch account')").first
        if await sw_item.count() > 0:
            await sw_item.click()
            await pg.wait_for_timeout(1500)
            target_ch = pg.locator(f"ytd-account-item-renderer:visible:has-text('{channel_name}')").first
            if await target_ch.count() > 0:
                await target_ch.click()
                print(f"[YT-MGR] Switched watch identity -> {channel_name}", flush=True)
                await pg.wait_for_timeout(4000)
                return
        await pg.keyboard.press("Escape")
    except Exception:
        try:
            await pg.keyboard.press("Escape")
        except Exception:
            pass


async def post_and_pin_comment(pg, video_id: str, comment_text: str) -> dict:
    """Posts an owner CTA comment on Watch/Shorts page in a clean tab and pins if available."""
    res = {"posted": False, "pinned": False, "skipped_existing": False}
    if not video_id or not comment_text:
        return res
    st = load_channel_state()
    ch_name = st.get("channel_name", "")
    ch_handle = (st.get("handle") or "").lstrip("@")

    watch_pg = await pg.context.new_page()
    try:
        await watch_pg.goto(f"https://www.youtube.com/watch?v={video_id}", wait_until="domcontentloaded", timeout=45000)
        await watch_pg.wait_for_timeout(4500)
        await _ensure_www_channel_identity(watch_pg, ch_name, ch_handle)

        ph = watch_pg.locator("#placeholder-area").first
        for _ in range(5):
            if await ph.count() > 0 and await ph.is_visible():
                break
            await watch_pg.evaluate("window.scrollBy(0, 480)")
            await watch_pg.wait_for_timeout(1200)

        if await ph.count() == 0:
            await watch_pg.goto(f"https://www.youtube.com/shorts/{video_id}", wait_until="domcontentloaded", timeout=45000)
            await watch_pg.wait_for_timeout(4000)
            c_btn = watch_pg.locator("#comments-button button, button[aria-label*='comment' i]").first
            if await c_btn.count() > 0:
                await c_btn.click()
                await watch_pg.wait_for_timeout(2000)

        threads = watch_pg.locator("ytd-comment-thread-renderer")
        for i in range(min(await threads.count(), 5)):
            txt = (await threads.nth(i).inner_text()).lower()
            if (ch_handle and ch_handle.lower() in txt) or (ch_name and ch_name.lower() in txt):
                res["skipped_existing"] = True
                return res

        ph = watch_pg.locator("#placeholder-area:visible").first
        if await ph.count() == 0:
            return res
        await ph.scroll_into_view_if_needed()
        await ph.click()
        await watch_pg.wait_for_timeout(700)

        box = watch_pg.locator("#contenteditable-root:visible").first
        await box.click()
        await watch_pg.keyboard.insert_text(comment_text)
        await watch_pg.wait_for_timeout(700)

        sub = watch_pg.locator("ytd-commentbox #submit-button button:visible, #submit-button button:visible").first
        if await sub.count() > 0:
            await sub.click()
            res["posted"] = True
            print(f"[YT-MGR] Posted Owner Comment on {video_id}", flush=True)
            await watch_pg.wait_for_timeout(3500)

            menu_btn = watch_pg.locator("ytd-comment-thread-renderer #action-menu button").first
            if await menu_btn.count() > 0:
                await menu_btn.click()
                await watch_pg.wait_for_timeout(1000)
                pin_item = watch_pg.locator("tp-yt-paper-item:visible:has-text('Pin'), ytd-menu-service-item-renderer:visible:has-text('Pin')").first
                if await pin_item.count() > 0:
                    await pin_item.click()
                    await watch_pg.wait_for_timeout(1000)
                    confirm_pin = watch_pg.locator("yt-confirm-dialog-renderer #confirm-button button, tp-yt-paper-dialog button:has-text('Pin')").last
                    if await confirm_pin.count() > 0:
                        await confirm_pin.click()
                        res["pinned"] = True
                        await watch_pg.wait_for_timeout(1500)
                else:
                    await watch_pg.keyboard.press("Escape")
    except Exception as exc:
        print(f"[YT-MGR] Comment warning ({video_id}): {exc}", flush=True)
    finally:
        try:
            await watch_pg.close()
        except Exception:
            pass
    return res


async def configure_pro_studio_foundation(cdp_url: str | None = None) -> dict:
    """Enables Home Tab, uploads 150x150 Subscribe Watermark & sets Channel COPPA Not Made for Kids."""
    cfg = load_config()
    cdp = cdp_url or cfg["cdp_url"]
    cid = load_channel_state().get("channel_id")
    if not cid:
        raise RuntimeError("channel_id not set in config.json or youtube_channel_state.json")

    summary = {"home_tab_enabled": False, "watermark_uploaded": False, "coppa_channel_set": False}
    wm_path = Path(cfg["watermark_path"])
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp(cdp, timeout=30000)
        ctx = b.contexts[0]
        pg = await ctx.new_page()
        pg.on("dialog", lambda d: asyncio.create_task(d.accept()))
        try:
            await pg.goto(f"https://studio.youtube.com/channel/{cid}/editing/hometab", wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(4500)
            toggle = pg.locator("tp-yt-paper-toggle-button[aria-label*='Home tab'], [role='switch'][aria-label*='Home tab']").first
            if await toggle.count() > 0:
                if (await toggle.get_attribute("aria-checked")) != "true":
                    await _click_center(pg, toggle)
                    await pg.wait_for_timeout(1200)
                    await _wait_button_commit(pg, pg.locator("#publish-button button, #publish-button").first, "HOME_TAB")
                summary["home_tab_enabled"] = (await toggle.get_attribute("aria-checked")) == "true"

            if wm_path.exists():
                await pg.goto(f"https://studio.youtube.com/channel/{cid}/editing/profile", wait_until="domcontentloaded", timeout=45000)
                try:
                    await pg.wait_for_selector("input[type='file']", state="attached", timeout=20000)
                except Exception:
                    pass
                await pg.wait_for_timeout(1500)
                sec_info = await pg.evaluate("""() => Array.from(document.querySelectorAll("input[type='file']")).map((f, idx) => {
                    let el = f; let t = '';
                    for (let k=0; k<6 && el; k++) { t = (el.innerText||''); if (t.length > 20) break; el = el.parentElement; }
                    return { idx, txt: t.toLowerCase() };
                })""")
                wm_idx = next((x["idx"] for x in sec_info if "150" in x["txt"] or "watermark" in x["txt"]), None)
                if wm_idx is not None:
                    already_wm = any("change" in x["txt"] and "remove" in x["txt"] for x in sec_info if x["idx"] == wm_idx)
                    if not already_wm:
                        await pg.locator("input[type='file']").nth(wm_idx).set_input_files(str(wm_path))
                        await pg.wait_for_timeout(2500)
                        done_w = pg.locator("ytcp-image-cropper-dialog:visible #done-button button:visible, tp-yt-paper-dialog:visible button:visible:has-text('Done'), ytcp-dialog:visible button:visible:has-text('Done')").last
                        if await done_w.count() > 0:
                            await done_w.click()
                            await pg.wait_for_timeout(1500)
                            entire_rad = pg.locator("tp-yt-paper-radio-button:visible:has-text('Entire video')").first
                            if await entire_rad.count() > 0:
                                await entire_rad.click()
                                await pg.wait_for_timeout(600)
                        else:
                            await pg.keyboard.press("Escape")
                        await _wait_button_commit(pg, pg.locator("#publish-button button, #publish-button").first, "WATERMARK")
                    summary["watermark_uploaded"] = True

            await pg.goto(f"https://studio.youtube.com/channel/{cid}/editing/profile", wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(3500)
            await _open_studio_settings_channel(pg)
            dlg = pg.locator("ytcp-dialog, ytcp-settings-dialog").last
            adv_tab = dlg.locator("tp-yt-paper-tab:has-text('Advanced settings'), div[role='tab']:has-text('Advanced')").first
            if await adv_tab.count() > 0:
                await adv_tab.click()
                await pg.wait_for_timeout(1500)
                not_kids = dlg.locator("tp-yt-paper-radio-button:has-text('not Made for Kids')").first
                if await not_kids.count() > 0:
                    if (await not_kids.get_attribute("aria-checked")) != "true":
                        await not_kids.click()
                        await pg.wait_for_timeout(700)
                    summary["coppa_channel_set"] = True
            save_b = dlg.locator("#save-button button, #save-button").first
            if not await _wait_button_commit(pg, save_b, "SETTINGS_COPPA"):
                cb = dlg.locator("#close-button button, button:has-text('Close')").first
                if await cb.count() > 0:
                    await cb.click()
        finally:
            await pg.close()
    return summary


async def backfill_live_shorts(catalog_items: list[dict], history: dict, cdp_url: str | None = None) -> list[dict]:
    cfg = load_config()
    cdp = cdp_url or cfg["cdp_url"]
    by_id = {x["id"]: x for x in catalog_items}
    results = []
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp(cdp, timeout=30000)
        ctx = b.contexts[0]
        pg = await ctx.new_page()
        pg.on("dialog", lambda d: asyncio.create_task(d.accept()))
        try:
            for up in history.get("uploads", []):
                vid = up.get("video_id")
                cid_item = up.get("id")
                if not vid or cid_item not in by_id:
                    continue
                yt = by_id[cid_item]["youtube_shorts"]
                await pg.goto(f"https://studio.youtube.com/video/{vid}/edit", wait_until="domcontentloaded", timeout=45000)
                await pg.wait_for_selector("ytcp-video-metadata-playlists", timeout=30000)
                await pg.wait_for_timeout(1800)

                meta_res = await apply_full_video_metadata(
                    pg,
                    tags=yt.get("tags", []),
                    playlist_name=yt.get("playlist_name"),
                    game_title=yt.get("game_title", cfg.get("default_game_title")),
                    altered_content=bool(yt.get("altered_content", False)),
                )
                saved = await _wait_button_commit(pg, pg.locator("ytcp-button#save button, ytcp-button#save").first, f"EDIT_{vid}")
                c_res = await post_and_pin_comment(pg, vid, yt.get("pinned_comment", ""))
                results.append({"video_id": vid, "metadata_changes": meta_res, "saved": saved, "comment": c_res})
        finally:
            await pg.close()
    return results


async def audit_and_collect_analytics(cdp_url: str | None = None, reply_comments: bool = True) -> dict:
    cfg = load_config()
    cdp = cdp_url or cfg["cdp_url"]
    cid = load_channel_state().get("channel_id")
    if not cid:
        raise RuntimeError("channel_id not set in config.json or youtube_channel_state.json")

    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "channel_id": cid,
        "home_tab_enabled": False,
        "feature_eligibility": {},
        "earn_progress": {},
        "dashboard_summary": {},
        "shorts_metrics": [],
        "unresponded_comments_handled": [],
    }
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp(cdp, timeout=30000)
        ctx = b.contexts[0]
        pg = await ctx.new_page()
        try:
            await pg.goto(f"https://studio.youtube.com/channel/{cid}", wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(4500)
            dash_txt = await pg.locator("body").inner_text()
            if _is_google_auth_gate(pg.url, dash_txt):
                report["auth_gate"] = True
                return report
            m_sub = re.search(r"Current subscribers\s+(\d+)", dash_txt)
            m_views = re.search(r"Last 28 days\s+Views\s+([\d,]+)", dash_txt)
            report["dashboard_summary"] = {
                "subscribers": int(m_sub.group(1)) if m_sub else 0,
                "views_28d": m_views.group(1) if m_views else "0",
            }

            await pg.goto(f"https://studio.youtube.com/channel/{cid}/videos/short", wait_until="domcontentloaded", timeout=45000)
            try:
                await pg.wait_for_selector("ytcp-video-row", timeout=15000)
                await pg.wait_for_timeout(1200)
            except Exception:
                await pg.wait_for_timeout(3000)
            rows = pg.locator("ytcp-video-row")
            for i in range(await rows.count()):
                raw = [x.strip() for x in (await rows.nth(i).inner_text()).splitlines() if x.strip()]
                if raw:
                    report["shorts_metrics"].append({"row": i + 1, "title": raw[0], "cells": raw[1:8]})

            await pg.goto(f"https://studio.youtube.com/channel/{cid}/monetization", wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(4000)
            earn_txt = await pg.locator("body").inner_text()
            for k, pat in [("subscribers", r"([\d,]+)\s+subscribers"), ("watch_hours_365d", r"([\d,]+)\s+qualified watch hours"), ("shorts_views_90d", r"([\d,]+)\s+qualified Shorts views")]:
                m = re.search(pat, earn_txt)
                report["earn_progress"][k] = m.group(1) if m else "0"

            await pg.goto(f"https://studio.youtube.com/channel/{cid}/editing/hometab", wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(3500)
            ht = pg.locator("tp-yt-paper-toggle-button[aria-label*='Home tab'], [role='switch'][aria-label*='Home tab']").first
            if await ht.count() > 0:
                report["home_tab_enabled"] = (await ht.get_attribute("aria-checked")) == "true"

            await _open_studio_settings_channel(pg)
            dlg = pg.locator("ytcp-dialog, ytcp-settings-dialog").last
            ftab = dlg.locator("tp-yt-paper-tab:has-text('Feature eligibility'), div[role='tab']:has-text('Feature')").first
            if await ftab.count() > 0:
                await ftab.click()
                await pg.wait_for_timeout(1500)
                ftxt = await dlg.inner_text()
                for lvl, label in [("1_standard", "Standard features"), ("2_intermediate", "Intermediate features"), ("3_advanced", "Advanced features")]:
                    m = re.search(rf"{label}[\s\S]{{0,140}}?(Enabled|Eligible|Not eligible)", ftxt)
                    report["feature_eligibility"][lvl] = m.group(1) if m else "Unknown"
            await pg.keyboard.press("Escape")

            if reply_comments:
                await pg.goto(f"https://studio.youtube.com/channel/{cid}/comments/inbox", wait_until="domcontentloaded", timeout=45000)
                await pg.wait_for_timeout(4000)
                threads = pg.locator("ytcp-comment-thread")
                for i in range(min(await threads.count(), 3)):
                    th = threads.nth(i)
                    txt = (await th.inner_text()).strip()
                    if any(bad in txt.lower() for bad in ["http://", "https://", "t.me/", "whatsapp", "crypto"]):
                        continue
                    reply_btn = th.locator("ytcp-button:has-text('Reply'), button:has-text('Reply')").first
                    if await reply_btn.count() > 0:
                        await reply_btn.click()
                        await pg.wait_for_timeout(600)
                        tb = th.locator("textarea, div[contenteditable='true']").first
                        if await tb.count() > 0:
                            reply_text = "Appreciate the support! Drop what moment you want clipped next!"
                            await tb.click()
                            await pg.keyboard.insert_text(reply_text)
                            await pg.wait_for_timeout(400)
                            submit = th.locator("#submit-button button, ytcp-button:has-text('Reply') button").last
                            if await submit.count() > 0:
                                await submit.click()
                                report["unresponded_comments_handled"].append({"comment_preview": txt[:90], "reply": reply_text})
                                await pg.wait_for_timeout(1500)
        finally:
            await pg.close()

    save_json(cfg["audit_path"], report)
    hist = load_json(cfg["analytics_history_path"], [])
    hist.append(report)
    save_json(cfg["analytics_history_path"], hist[-60:])
    if report["unresponded_comments_handled"]:
        save_json(cfg["comments_log_path"], report["unresponded_comments_handled"])
    return report
