"""
Portable YouTube Pro Channel Operations & Analytics Manager.

Implements all 7 pro creator workflows via Chrome CDP + Playwright:
  1. Studio Channel Health & Feature Eligibility Audit
  2. Home Tab, 150×150 Subscribe Watermark & Channel COPPA defaults
  3. Complete per-video metadata (Playlist, Altered Content, Category, Game Title, Language, Tags)
  4. Owner CTA Comment + Pin attempt (clean watch tab + channel identity verification)
  5. Studio Analytics & Unresponded Comments Inbox Loop
"""

from __future__ import annotations

import asyncio
import datetime
import re
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypeVar

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import is_cdp_available, load_config, load_json, resolve_cdp_url, save_json
from constants import (
    AUTH_GATE_BODY_PATTERNS,
    AUTH_GATE_URL_PATTERN,
    CDP_CONNECT_TIMEOUT_MS,
    COMMENT_POST_SETTLE_MS,
    COMMENT_SPAM_KEYWORDS,
    DEFAULT_REPLY_TEXT,
    DROPDOWN_SETTLE_MS,
    FILE_INPUT_ATTACH_TIMEOUT_MS,
    GAME_AUTOCOMPLETE_SETTLE_MS,
    IDENTITY_SWITCH_SETTLE_MS,
    LONG_SETTLE_MS,
    MAX_ANALYTICS_HISTORY_ENTRIES,
    MAX_COMMENT_THREADS_TO_SCAN,
    MAX_INBOX_REPLIES_PER_RUN,
    MAX_TAGS_STRING_LENGTH,
    MEDIUM_SETTLE_MS,
    MODAL_DISMISS_MS,
    PAGE_LOAD_TIMEOUT_MS,
    SAVE_BUTTON_POLL_S,
    SCROLL_SETTLE_MS,
    SETTINGS_OPEN_SETTLE_MS,
    SHORT_SETTLE_MS,
    STEP_NEXT_SETTLE_MS,
    STUDIO_SETTLE_MS,
    WATERMARK_ATTACH_SETTLE_MS,
)
from constants import (
    StudioSelectors as S,
)
from exceptions import AuthGateError, CDPConnectionError
from logger import get_logger

log = get_logger(__name__)
T = TypeVar("T")

__all__ = [
    "is_cdp_available",
    "load_channel_state",
    "save_channel_state",
    "apply_full_video_metadata",
    "post_and_pin_comment",
    "configure_pro_studio_foundation",
    "backfill_live_shorts",
    "audit_and_collect_analytics",
]


# ═══════════════════════════════════════════════════════════════════════
# State & Auth Helpers
# ═══════════════════════════════════════════════════════════════════════

def load_channel_state() -> dict[str, Any]:
    """Load channel state, merging in config defaults for missing fields."""
    cfg = load_config()
    st = load_json(cfg["channel_state_path"], {})
    if not st.get("channel_id") and cfg.get("channel_id"):
        st["channel_id"] = cfg["channel_id"]
    if not st.get("channel_name") and cfg.get("channel_name"):
        st["channel_name"] = cfg["channel_name"]
    if not st.get("handle") and cfg.get("channel_handle"):
        st["handle"] = cfg["channel_handle"]
    return st


def save_channel_state(state: dict[str, Any]) -> None:
    """Persist channel state to disk."""
    cfg = load_config()
    save_json(cfg["channel_state_path"], state)


def _is_google_auth_gate(url: str, body_text: str) -> bool:
    """Detect Google authentication gates (2FA, re-login, verify)."""
    if AUTH_GATE_URL_PATTERN in url.lower():
        return True
    t = body_text.lower()
    return any(p in t for p in AUTH_GATE_BODY_PATTERNS)


async def _assert_not_auth_gate(pg: Any) -> None:
    """Raise :class:`AuthGateError` immediately if Google challenges automation."""
    body_text = await pg.locator("body").inner_text()
    if _is_google_auth_gate(pg.url, body_text):
        raise AuthGateError(pg.url)


async def _retry_async(
    coro_factory: Callable[[], Awaitable[T]],
    attempts: int = 2,
    delay_ms: int = DROPDOWN_SETTLE_MS,
    label: str = "CDP op",
) -> T:
    """Retry a transient async browser operation before propagating the error."""
    last_exc: Exception | None = None
    for idx in range(attempts):
        try:
            return await coro_factory()
        except AuthGateError:
            raise
        except Exception as exc:
            last_exc = exc
            if idx + 1 < attempts:
                log.debug("%s retry %d/%d after: %s", label, idx + 1, attempts - 1, exc)
                await asyncio.sleep(delay_ms / 1000.0)
    assert last_exc is not None
    raise last_exc


# ═══════════════════════════════════════════════════════════════════════
# DOM Helpers
# ═══════════════════════════════════════════════════════════════════════

async def _click_center(pg: Any, locator: Any) -> bool:
    """Click a Polymer element via bounding-box center (more reliable than .click)."""
    try:
        await locator.scroll_into_view_if_needed()
        await pg.wait_for_timeout(SHORT_SETTLE_MS)
        box = await locator.bounding_box()
        if box and box["width"] > 0 and box["height"] > 0:
            await pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            return True
        await locator.click()
        return True
    except Exception:
        return False


async def _open_studio_settings_channel(pg: Any) -> None:
    """Dismiss Studio backdrop overlays and navigate to Settings → Channel."""
    for _ in range(4):
        if await pg.locator(S.OPENED_BACKDROP).count() == 0:
            break
        dismiss = pg.locator(S.DISMISS_BUTTONS).last
        if await dismiss.count() > 0:
            await dismiss.click()
        else:
            await pg.keyboard.press("Escape")
        await pg.wait_for_timeout(MODAL_DISMISS_MS)

    await pg.evaluate(
        "() => document.querySelectorAll('tp-yt-iron-overlay-backdrop.opened').forEach(b => {"
        " if (!document.querySelector('ytcp-dialog, tp-yt-paper-dialog[aria-hidden=\"false\"]')) b.remove(); })"
    )
    await pg.locator(S.SETTINGS_ITEM).first.click()
    await pg.wait_for_timeout(SETTINGS_OPEN_SETTLE_MS)
    await pg.locator(S.CHANNEL_TAB).first.click()
    await pg.wait_for_timeout(LONG_SETTLE_MS)


async def _wait_button_commit(pg: Any, btn_locator: Any, label: str, max_wait: int = SAVE_BUTTON_POLL_S) -> bool:
    """Click a save/publish button and wait until it becomes disabled (saved)."""
    if await btn_locator.count() == 0:
        return False
    if (await btn_locator.get_attribute("aria-disabled")) == "true":
        return False
    await btn_locator.click()
    log.info("[%s] Saving...", label)
    for _ in range(max_wait):
        await pg.wait_for_timeout(DROPDOWN_SETTLE_MS)
        if (await btn_locator.get_attribute("aria-disabled")) == "true":
            log.info("[%s] Saved.", label)
            await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
            return True
    return True


# ═══════════════════════════════════════════════════════════════════════
# Metadata Helpers
# ═══════════════════════════════════════════════════════════════════════

async def _set_playlist_in_form(pg: Any, playlist_name: str | None) -> bool:
    """Select a playlist in the upload/edit dialog."""
    if not playlist_name:
        return False
    trig = pg.locator(S.PLAYLIST_TRIGGER).first
    if await trig.count() == 0 or not await _click_center(pg, trig):
        return False
    dlg = pg.locator(S.PLAYLIST_DIALOG).last
    try:
        await dlg.wait_for(state="visible", timeout=10000)
    except Exception:
        return False
    await pg.wait_for_timeout(MEDIUM_SETTLE_MS)

    changed = False
    row = dlg.get_by_text(playlist_name, exact=True).first
    if await row.count() > 0:
        already = await row.evaluate(
            """el => {
            const box = el.closest('label, li, .item') || el.parentElement;
            const cb = box
                ? box.querySelector('ytcp-checkbox-lit, tp-yt-paper-checkbox, [role="checkbox"]')
                : null;
            if (!cb) return false;
            return !!(
                cb.hasAttribute('checked')
                || cb.getAttribute('aria-checked') === 'true'
                || cb.querySelector('[aria-checked="true"]')
            );
        }"""
        )
        if not already:
            await row.click()
            changed = True
            await pg.wait_for_timeout(MODAL_DISMISS_MS)
            log.info("Selected Playlist → '%s'", playlist_name)

    done_b = dlg.locator(S.PLAYLIST_DONE).last
    if await done_b.count() > 0 and (await done_b.get_attribute("aria-disabled")) != "true":
        await done_b.click()
        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
    try:
        if await dlg.is_visible():
            await pg.keyboard.press("Escape")
            await pg.wait_for_timeout(MODAL_DISMISS_MS)
    except Exception:
        pass
    return changed


async def _expand_show_more(pg: Any, scope_selector: str = "") -> bool:
    """Click 'Show more' in the upload/edit dialog."""
    prefix = f"{scope_selector} " if scope_selector else ""
    sm = pg.locator(f"{prefix}{S.SHOW_MORE}").first
    if await sm.count() > 0:
        await sm.scroll_into_view_if_needed()
        await pg.wait_for_timeout(SHORT_SETTLE_MS)
        await sm.click()
        await pg.wait_for_timeout(LONG_SETTLE_MS)
        return True
    return False


async def _ensure_gaming_and_us_language(
    pg: Any,
    scope_selector: str = "",
    category_name: str = "Gaming",
    target_lang: str = "English (United States)",
) -> bool:
    """Set video category and both language dropdowns to the configured target language."""
    changed = False
    prefix = f"{scope_selector} " if scope_selector else ""
    base_lang = target_lang.split("(")[0].strip()
    try:
        cat_trig = pg.locator(f"{prefix}{S.CATEGORY_TRIGGER}").first
        if await cat_trig.count() > 0:
            cat_txt = (await cat_trig.inner_text()).strip()
            if category_name.lower() not in cat_txt.lower():
                await _click_center(pg, cat_trig)
                await pg.wait_for_timeout(DROPDOWN_SETTLE_MS)
                opt = pg.locator(f"tp-yt-paper-item:visible:has-text('{category_name}')").first
                if await opt.count() > 0:
                    await opt.click()
                    await pg.wait_for_timeout(SCROLL_SETTLE_MS)
                    log.info("Set Category → %s", category_name)
                    changed = True

        for lang_label in ("Video language", "Title and description language"):
            ltrig = pg.locator(f"{prefix}{S.LANG_DROPDOWN_TEMPLATE.format(label=lang_label)}").first
            if await ltrig.count() > 0:
                ltxt = (await ltrig.inner_text()).strip()
                if base_lang.lower() not in ltxt.lower():
                    await _click_center(pg, ltrig)
                    await pg.wait_for_timeout(DROPDOWN_SETTLE_MS)
                    eopt = pg.locator(f"tp-yt-paper-item:visible:has-text('{target_lang}')").first
                    if await eopt.count() == 0:
                        eopt = pg.locator(f"tp-yt-paper-item:visible:text-is('{base_lang}')").first
                    if await eopt.count() > 0:
                        await eopt.scroll_into_view_if_needed()
                        await eopt.click()
                        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
                        log.info("Set %s → %s", lang_label, target_lang)
                        changed = True
                    else:
                        await pg.keyboard.press("Escape")
    except Exception as exc:
        log.debug("Category/Language check note: %s", exc)
    return changed


async def _set_game_title(pg: Any, game_title: str | None, scope_selector: str = "") -> bool:
    """Type and select an official Game Title from the autocomplete."""
    if not game_title:
        return False
    prefix = f"{scope_selector} " if scope_selector else ""
    inp = pg.locator(f"{prefix}{S.GAME_TITLE_INPUT}").first
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
        await pg.wait_for_timeout(GAME_AUTOCOMPLETE_SETTLE_MS)
        opt = pg.locator(S.GAME_AUTOCOMPLETE_OPTION.format(title=game_title)).first
        if await opt.count() > 0:
            await opt.click()
            await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
            log.info("Selected Game Title → '%s'", game_title)
            return True
        await pg.keyboard.press("Tab")
        return True
    except Exception:
        return False


async def _set_altered_content(pg: Any, altered_content: bool = False, scope_selector: str = "") -> bool:
    """Set the Altered Content radio button."""
    prefix = f"{scope_selector} " if scope_selector else ""
    selector = S.ALTERED_YES if altered_content else S.ALTERED_NO
    rad = pg.locator(f"{prefix}{selector}").first
    if await rad.count() == 0:
        return False
    try:
        if (await rad.get_attribute("aria-checked")) == "true":
            return False
        await rad.scroll_into_view_if_needed()
        await rad.click()
        await pg.wait_for_timeout(SHORT_SETTLE_MS)
        log.info("Altered Content → %s", "Yes" if altered_content else "No")
        return True
    except Exception:
        return False


async def _ensure_tags(pg: Any, tags: list[str], scope_selector: str = "") -> bool:
    """Insert tags into the Tags input field."""
    if not tags:
        return False
    prefix = f"{scope_selector} " if scope_selector else ""
    tags_inp = pg.locator(f"{prefix}{S.TAGS_INPUT}").first
    if await tags_inp.count() == 0:
        return False
    try:
        if await pg.locator(f"{prefix}{S.TAGS_CHIPS}").count() >= 4:
            return False
        await tags_inp.scroll_into_view_if_needed()
        await tags_inp.click()
        await pg.keyboard.insert_text(", ".join(tags)[:MAX_TAGS_STRING_LENGTH])
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(MODAL_DISMISS_MS)
        return True
    except Exception:
        return False


async def apply_full_video_metadata(
    pg: Any,
    tags: list[str] | None = None,
    playlist_name: str | None = None,
    game_title: str | None = None,
    altered_content: bool = False,
    scope_selector: str = "",
) -> dict[str, bool]:
    """Apply Playlist, Altered Content, Category/Language, Tags & Game Title.

    Returns:
        Dict of field names to whether they were changed.
    """
    cfg = load_config()
    gtitle = game_title if game_title is not None else cfg.get("default_game_title")
    cat = cfg.get("default_category", "Gaming")
    lang = cfg.get("video_language", "English (United States)")

    changes: dict[str, bool] = {
        "playlist": False,
        "cat_lang": False,
        "altered": False,
        "tags": False,
        "game_title": False,
    }
    if playlist_name:
        changes["playlist"] = await _set_playlist_in_form(pg, playlist_name)
    await _expand_show_more(pg, scope_selector=scope_selector)
    changes["altered"] = await _set_altered_content(pg, altered_content=altered_content, scope_selector=scope_selector)
    if tags:
        changes["tags"] = await _ensure_tags(pg, tags, scope_selector=scope_selector)
    changes["cat_lang"] = await _ensure_gaming_and_us_language(
        pg, scope_selector=scope_selector, category_name=cat, target_lang=lang,
    )
    if gtitle:
        changes["game_title"] = await _set_game_title(pg, gtitle, scope_selector=scope_selector)
    return changes


# ═══════════════════════════════════════════════════════════════════════
# Comment Posting
# ═══════════════════════════════════════════════════════════════════════

async def _ensure_www_channel_identity(pg: Any, channel_name: str, handle: str) -> None:
    """Switch YouTube watch page identity to the brand channel if needed."""
    if not channel_name and not handle:
        return
    try:
        av_btn = pg.locator(S.AVATAR_BUTTON).first
        if await av_btn.count() == 0:
            return
        await av_btn.click()
        await pg.wait_for_timeout(SCROLL_SETTLE_MS)
        popup_txt = (await pg.locator(S.ACCOUNT_MENU_POPUP).last.inner_text()).lower()
        if (handle and handle.lstrip("@").lower() in popup_txt) or (channel_name and channel_name.lower() in popup_txt):
            await pg.keyboard.press("Escape")
            return
        sw_item = pg.locator(S.SWITCH_ACCOUNT).first
        if await sw_item.count() > 0:
            await sw_item.click()
            await pg.wait_for_timeout(LONG_SETTLE_MS)
            target_ch = pg.locator(S.ACCOUNT_ITEM_TEMPLATE.format(name=channel_name)).first
            if await target_ch.count() > 0:
                await target_ch.click()
                log.info("Switched watch identity → %s", channel_name)
                await pg.wait_for_timeout(IDENTITY_SWITCH_SETTLE_MS)
                return
        await pg.keyboard.press("Escape")
    except Exception:
        try:
            await pg.keyboard.press("Escape")
        except Exception:
            pass


async def post_and_pin_comment(pg: Any, video_id: str, comment_text: str) -> dict[str, bool]:
    """Post an owner CTA comment in a clean tab and attempt pinning.

    Args:
        pg: Playwright page (from Studio context — a new tab is opened).
        video_id: YouTube video ID.
        comment_text: The comment to post.

    Returns:
        Dict with posted, pinned, skipped_existing booleans.
    """
    res: dict[str, bool] = {"posted": False, "pinned": False, "skipped_existing": False}
    if not video_id or not comment_text:
        return res

    st = load_channel_state()
    ch_name = st.get("channel_name", "")
    ch_handle = (st.get("handle") or "").lstrip("@")

    watch_pg = await pg.context.new_page()
    try:
        await _retry_async(
            lambda: watch_pg.goto(
                f"https://www.youtube.com/watch?v={video_id}",
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            ),
            label="Watch navigate",
        )
        await watch_pg.wait_for_timeout(STUDIO_SETTLE_MS)
        await _ensure_www_channel_identity(watch_pg, ch_name, ch_handle)

        ph = watch_pg.locator(S.COMMENT_PLACEHOLDER).first
        for _ in range(5):
            if await ph.count() > 0 and await ph.is_visible():
                break
            await watch_pg.evaluate("window.scrollBy(0, 480)")
            await watch_pg.wait_for_timeout(SCROLL_SETTLE_MS)

        if await ph.count() == 0:
            await watch_pg.goto(
                f"https://www.youtube.com/shorts/{video_id}",
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )
            await watch_pg.wait_for_timeout(IDENTITY_SWITCH_SETTLE_MS)
            c_btn = watch_pg.locator(S.SHORTS_COMMENT_BUTTON).first
            if await c_btn.count() > 0:
                await c_btn.click()
                await watch_pg.wait_for_timeout(SETTINGS_OPEN_SETTLE_MS)

        threads = watch_pg.locator(S.COMMENT_THREADS)
        for i in range(min(await threads.count(), MAX_COMMENT_THREADS_TO_SCAN)):
            txt = (await threads.nth(i).inner_text()).lower()
            if (ch_handle and ch_handle.lower() in txt) or (ch_name and ch_name.lower() in txt):
                res["skipped_existing"] = True
                log.debug("Owner comment already exists on %s", video_id)
                return res

        ph = watch_pg.locator(f"{S.COMMENT_PLACEHOLDER}:visible").first
        if await ph.count() == 0:
            return res
        await ph.scroll_into_view_if_needed()
        await ph.click()
        await watch_pg.wait_for_timeout(MEDIUM_SETTLE_MS)

        box = watch_pg.locator(S.COMMENT_EDITABLE).first
        await box.click()
        await watch_pg.keyboard.insert_text(comment_text)
        await watch_pg.wait_for_timeout(MEDIUM_SETTLE_MS)

        sub = watch_pg.locator(S.COMMENT_SUBMIT).first
        if await sub.count() > 0:
            await sub.click()
            res["posted"] = True
            log.info("Posted Owner Comment on %s", video_id)
            await watch_pg.wait_for_timeout(COMMENT_POST_SETTLE_MS)

            menu_btn = watch_pg.locator(S.COMMENT_MENU).first
            if await menu_btn.count() > 0:
                await menu_btn.click()
                await watch_pg.wait_for_timeout(DROPDOWN_SETTLE_MS)
                pin_item = watch_pg.locator(S.PIN_ITEM).first
                if await pin_item.count() > 0:
                    await pin_item.click()
                    await watch_pg.wait_for_timeout(DROPDOWN_SETTLE_MS)
                    confirm_pin = watch_pg.locator(S.PIN_CONFIRM).last
                    if await confirm_pin.count() > 0:
                        await confirm_pin.click()
                        res["pinned"] = True
                        await watch_pg.wait_for_timeout(LONG_SETTLE_MS)
                else:
                    await watch_pg.keyboard.press("Escape")
    except Exception as exc:
        log.warning("Comment warning (%s): %s", video_id, exc)
    finally:
        try:
            await watch_pg.close()
        except Exception:
            pass
    return res


# ═══════════════════════════════════════════════════════════════════════
# Studio Foundation (Home Tab, Watermark, COPPA)
# ═══════════════════════════════════════════════════════════════════════

async def configure_pro_studio_foundation(cdp_url: str | None = None) -> dict[str, bool]:
    """Enable Home Tab, upload Subscribe Watermark, and set channel COPPA.

    Returns:
        Dict with home_tab_enabled, watermark_uploaded, coppa_channel_set booleans.

    Raises:
        CDPConnectionError: If Chrome CDP is offline or ``channel_id`` is unset.
        AuthGateError: If Google auth verification blocks Studio.
    """
    cfg = load_config()
    cdp = resolve_cdp_url(cdp_url or cfg["cdp_url"])
    cid = load_channel_state().get("channel_id")
    if not cid:
        raise CDPConnectionError(cdp, "channel_id not set in config.json or state")
    if not is_cdp_available(cdp):
        raise CDPConnectionError(cdp, "Chrome remote debugging endpoint unreachable")

    summary: dict[str, bool] = {"home_tab_enabled": False, "watermark_uploaded": False, "coppa_channel_set": False}
    wm_path = Path(cfg["watermark_path"])

    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
        if not b.contexts:
            raise CDPConnectionError(cdp, "Chrome has no active browser context")
        pg = await b.contexts[0].new_page()
        pg.on("dialog", lambda d: asyncio.create_task(d.accept()))
        try:
            # Home Tab
            await _retry_async(
                lambda: pg.goto(
                    f"https://studio.youtube.com/channel/{cid}/editing/hometab",
                    wait_until="domcontentloaded",
                    timeout=PAGE_LOAD_TIMEOUT_MS,
                ),
                label="Studio hometab",
            )
            await pg.wait_for_timeout(STUDIO_SETTLE_MS)
            await _assert_not_auth_gate(pg)

            toggle = pg.locator(S.HOME_TAB_TOGGLE).first
            if await toggle.count() > 0:
                if (await toggle.get_attribute("aria-checked")) != "true":
                    await _click_center(pg, toggle)
                    await pg.wait_for_timeout(SCROLL_SETTLE_MS)
                    await _wait_button_commit(pg, pg.locator(S.PUBLISH_BUTTON).first, "HOME_TAB")
                summary["home_tab_enabled"] = (await toggle.get_attribute("aria-checked")) == "true"

            # Watermark
            if wm_path.exists():
                await pg.goto(
                    f"https://studio.youtube.com/channel/{cid}/editing/profile",
                    wait_until="domcontentloaded",
                    timeout=PAGE_LOAD_TIMEOUT_MS,
                )
                try:
                    await pg.wait_for_selector(S.FILE_INPUT, state="attached", timeout=FILE_INPUT_ATTACH_TIMEOUT_MS)
                except Exception:
                    pass
                await pg.wait_for_timeout(LONG_SETTLE_MS)

                sec_info = await pg.evaluate(
                    """() => Array.from(document.querySelectorAll("input[type='file']")).map((f, idx) => {
                    let el = f; let t = '';
                    for (let k=0; k<6 && el; k++) {
                        t = (el.innerText||'');
                        if (t.length > 20) break;
                        el = el.parentElement;
                    }
                    return { idx, txt: t.toLowerCase() };
                })"""
                )
                wm_keywords = ("150", "watermark", "display time", "entire video")
                wm_idx = next(
                    (x["idx"] for x in sec_info if any(k in x["txt"] for k in wm_keywords)),
                    None,
                )
                if wm_idx is not None:
                    already_wm = any(
                        "change" in x["txt"] and "remove" in x["txt"]
                        for x in sec_info
                        if x["idx"] == wm_idx
                    )
                    if not already_wm:
                        await pg.locator(S.FILE_INPUT).nth(wm_idx).set_input_files(str(wm_path))
                        await pg.wait_for_timeout(WATERMARK_ATTACH_SETTLE_MS)
                        done_w = pg.locator(S.WATERMARK_CROP_DONE).last
                        if await done_w.count() > 0:
                            await done_w.click()
                            await pg.wait_for_timeout(LONG_SETTLE_MS)
                            entire_rad = pg.locator(S.ENTIRE_VIDEO_RADIO).first
                            if await entire_rad.count() > 0:
                                await entire_rad.click()
                                await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
                        else:
                            await pg.keyboard.press("Escape")
                        await _wait_button_commit(pg, pg.locator(S.PUBLISH_BUTTON).first, "WATERMARK")
                    summary["watermark_uploaded"] = True

            # COPPA
            await pg.goto(
                f"https://studio.youtube.com/channel/{cid}/editing/profile",
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )
            await pg.wait_for_timeout(COMMENT_POST_SETTLE_MS)
            await _open_studio_settings_channel(pg)
            dlg = pg.locator(S.SETTINGS_DIALOG).last
            adv_tab = dlg.locator(S.ADVANCED_TAB).first
            if await adv_tab.count() > 0:
                await adv_tab.click()
                await pg.wait_for_timeout(LONG_SETTLE_MS)
                not_kids = dlg.locator(S.NOT_FOR_KIDS_CHANNEL).first
                if await not_kids.count() > 0:
                    if (await not_kids.get_attribute("aria-checked")) != "true":
                        await not_kids.click()
                        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
                    summary["coppa_channel_set"] = True
            save_b = dlg.locator(S.SAVE_SETTINGS).first
            if not await _wait_button_commit(pg, save_b, "SETTINGS_COPPA"):
                cb = dlg.locator(S.CLOSE_SETTINGS).first
                if await cb.count() > 0:
                    await cb.click()
        finally:
            await pg.close()
    return summary


# ═══════════════════════════════════════════════════════════════════════
# Backfill Live Shorts
# ═══════════════════════════════════════════════════════════════════════

async def backfill_live_shorts(
    catalog_items: list[dict],
    history: dict[str, Any],
    cdp_url: str | None = None,
) -> list[dict[str, Any]]:
    """Apply full metadata and CTA comments to already-published Shorts.

    Returns:
        List of result dicts per video.

    Raises:
        CDPConnectionError: If Chrome CDP is unreachable or has no active context.
        AuthGateError: If Google auth verification blocks Studio.
    """
    cfg = load_config()
    cdp = resolve_cdp_url(cdp_url or cfg["cdp_url"])
    if not is_cdp_available(cdp):
        raise CDPConnectionError(cdp, "Chrome remote debugging endpoint unreachable")

    by_id = {x["id"]: x for x in catalog_items}
    results: list[dict[str, Any]] = []

    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
        if not b.contexts:
            raise CDPConnectionError(cdp, "Chrome has no active browser context")
        pg = await b.contexts[0].new_page()
        pg.on("dialog", lambda d: asyncio.create_task(d.accept()))
        try:
            for up in history.get("uploads", []):
                vid = up.get("video_id")
                cid_item = up.get("id")
                if not vid or cid_item not in by_id:
                    continue
                yt = by_id[cid_item]["youtube_shorts"]
                # Clear Studio SPA router before hopping between video edit pages
                await pg.goto("about:blank")
                await pg.goto(
                    f"https://studio.youtube.com/video/{vid}/edit",
                    wait_until="domcontentloaded",
                    timeout=PAGE_LOAD_TIMEOUT_MS,
                )
                await _assert_not_auth_gate(pg)
                await pg.wait_for_selector(S.PLAYLIST_METADATA, timeout=CDP_CONNECT_TIMEOUT_MS)
                await pg.wait_for_timeout(STEP_NEXT_SETTLE_MS)

                meta_res = await apply_full_video_metadata(
                    pg,
                    tags=yt.get("tags", []),
                    playlist_name=yt.get("playlist_name"),
                    game_title=yt.get("game_title", cfg.get("default_game_title")),
                    altered_content=bool(yt.get("altered_content", False)),
                )
                saved = await _wait_button_commit(pg, pg.locator(S.SAVE_BUTTON).first, f"EDIT_{vid}")
                c_res = await post_and_pin_comment(pg, vid, yt.get("pinned_comment", ""))
                results.append({"video_id": vid, "metadata_changes": meta_res, "saved": saved, "comment": c_res})
        finally:
            await pg.close()
    return results


# ═══════════════════════════════════════════════════════════════════════
# Analytics & Comments Audit
# ═══════════════════════════════════════════════════════════════════════

async def audit_and_collect_analytics(
    cdp_url: str | None = None,
    reply_comments: bool = True,
    channel_id_override: str | None = None,
) -> dict[str, Any]:
    """Scrape Studio Dashboard, Shorts metrics, Earn progress, and reply to comments.

    Returns:
        Comprehensive audit report dict.

    Raises:
        CDPConnectionError: If Chrome CDP is unreachable or ``channel_id`` is unset.
        AuthGateError: If Google auth verification blocks Studio.
    """
    cfg = load_config()
    cdp = resolve_cdp_url(cdp_url or cfg["cdp_url"])
    cid = channel_id_override or load_channel_state().get("channel_id")
    if not cid:
        raise CDPConnectionError(cdp, "channel_id not set in config.json or state")
    if not is_cdp_available(cdp):
        raise CDPConnectionError(cdp, "Chrome remote debugging endpoint unreachable")

    report: dict[str, Any] = {
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
        b = await p.chromium.connect_over_cdp(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
        if not b.contexts:
            raise CDPConnectionError(cdp, "Chrome has no active browser context")
        pg = await b.contexts[0].new_page()
        try:
            await _retry_async(
                lambda: pg.goto(
                    f"https://studio.youtube.com/channel/{cid}",
                    wait_until="domcontentloaded",
                    timeout=PAGE_LOAD_TIMEOUT_MS,
                ),
                label="Studio dashboard",
            )
            await pg.wait_for_timeout(STUDIO_SETTLE_MS)
            await _assert_not_auth_gate(pg)

            dash_txt = await pg.locator("body").inner_text()
            m_sub = re.search(r"Current subscribers\s+(\d+)", dash_txt)
            m_views = re.search(r"Last 28 days\s+Views\s+([\d,]+)", dash_txt)
            report["dashboard_summary"] = {
                "subscribers": int(m_sub.group(1)) if m_sub else 0,
                "views_28d": m_views.group(1) if m_views else "0",
            }

            # Shorts content
            await pg.goto(
                f"https://studio.youtube.com/channel/{cid}/videos/short",
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )
            try:
                await pg.wait_for_selector(S.VIDEO_ROW, timeout=25000)
                await pg.wait_for_timeout(SCROLL_SETTLE_MS * 2)
            except Exception:
                await pg.wait_for_timeout(4000)
            rows = pg.locator(S.VIDEO_ROW)
            for i in range(await rows.count()):
                raw = [x.strip() for x in (await rows.nth(i).inner_text()).splitlines() if x.strip()]
                if raw:
                    report["shorts_metrics"].append({"row": i + 1, "title": raw[0], "cells": raw[1:8]})

            # Earn tab
            await pg.goto(
                f"https://studio.youtube.com/channel/{cid}/monetization",
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )
            await pg.wait_for_timeout(IDENTITY_SWITCH_SETTLE_MS)
            earn_txt = await pg.locator("body").inner_text()
            for k, pat in [
                ("subscribers", r"([\d,]+)\s+subscribers"),
                ("watch_hours_365d", r"([\d,]+)\s+qualified watch hours"),
                ("shorts_views_90d", r"([\d,]+)\s+qualified Shorts views"),
            ]:
                m = re.search(pat, earn_txt)
                report["earn_progress"][k] = m.group(1) if m else "0"

            # Home Tab check
            await pg.goto(
                f"https://studio.youtube.com/channel/{cid}/editing/hometab",
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )
            await pg.wait_for_timeout(COMMENT_POST_SETTLE_MS)
            ht = pg.locator(S.HOME_TAB_TOGGLE).first
            if await ht.count() > 0:
                report["home_tab_enabled"] = (await ht.get_attribute("aria-checked")) == "true"

            # Feature eligibility
            await _open_studio_settings_channel(pg)
            dlg = pg.locator(S.SETTINGS_DIALOG).last
            ftab = dlg.locator(S.FEATURE_TAB).first
            if await ftab.count() > 0:
                await ftab.click()
                await pg.wait_for_timeout(LONG_SETTLE_MS)
                ftxt = await dlg.inner_text()
                tiers = [
                    ("1_standard", "Standard features"),
                    ("2_intermediate", "Intermediate features"),
                    ("3_advanced", "Advanced features"),
                ]
                for lvl, label in tiers:
                    m = re.search(rf"{label}[\s\S]{{0,140}}?(Enabled|Eligible|Not eligible)", ftxt)
                    report["feature_eligibility"][lvl] = m.group(1) if m else "Unknown"
            await pg.keyboard.press("Escape")

            # Comments inbox
            if reply_comments:
                await pg.goto(
                    f"https://studio.youtube.com/channel/{cid}/comments/inbox",
                    wait_until="domcontentloaded",
                    timeout=PAGE_LOAD_TIMEOUT_MS,
                )
                await pg.wait_for_timeout(IDENTITY_SWITCH_SETTLE_MS)
                threads = pg.locator(S.INBOX_THREAD)
                for i in range(min(await threads.count(), MAX_INBOX_REPLIES_PER_RUN)):
                    th = threads.nth(i)
                    txt = (await th.inner_text()).strip()
                    if any(bad in txt.lower() for bad in COMMENT_SPAM_KEYWORDS):
                        continue
                    reply_btn = th.locator(S.INBOX_REPLY_BUTTON).first
                    if await reply_btn.count() > 0:
                        await reply_btn.click()
                        await pg.wait_for_timeout(MEDIUM_SETTLE_MS)
                        tb = th.locator(S.INBOX_REPLY_TEXTBOX).first
                        if await tb.count() > 0:
                            await tb.click()
                            await pg.keyboard.insert_text(DEFAULT_REPLY_TEXT)
                            await pg.wait_for_timeout(SHORT_SETTLE_MS)
                            submit = th.locator(S.INBOX_REPLY_SUBMIT).last
                            if await submit.count() > 0:
                                await submit.click()
                                report["unresponded_comments_handled"].append(
                                    {"comment_preview": txt[:90], "reply": DEFAULT_REPLY_TEXT},
                                )
                                await pg.wait_for_timeout(LONG_SETTLE_MS)
        finally:
            await pg.close()

    # Persist
    save_json(cfg["audit_path"], report)
    hist = load_json(cfg["analytics_history_path"], [])
    if not isinstance(hist, list):
        hist = []
    hist.append(report)
    save_json(cfg["analytics_history_path"], hist[-MAX_ANALYTICS_HISTORY_ENTRIES:])
    if report["unresponded_comments_handled"]:
        save_json(cfg["comments_log_path"], report["unresponded_comments_handled"])

    log.info(
        "Audit complete: subs=%s, views_28d=%s, shorts=%d, comments_replied=%d",
        report["dashboard_summary"].get("subscribers", 0),
        report["dashboard_summary"].get("views_28d", "0"),
        len(report["shorts_metrics"]),
        len(report["unresponded_comments_handled"]),
    )
    return report
