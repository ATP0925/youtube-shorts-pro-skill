# YouTube Studio & Watch DOM Gotchas (Engineering Reference)

> **Verified Working As Of:** November 2026 (`studio.youtube.com` Polymer / Lit DOM)
> Single source of truth for selectors: [`scripts/constants.py`](../scripts/constants.py) (`StudioSelectors` & `IGSelectors`).

---

1. **Polymer Backdrop Interception (`tp-yt-iron-overlay-backdrop.opened`):**
   Closing a modal quickly leaves an overlay backdrop active that intercepts clicks on `#settings-item`. Dismiss modals cleanly and prune orphaned backdrops:
   ```python
   await pg.evaluate(
       "() => document.querySelectorAll('tp-yt-iron-overlay-backdrop.opened').forEach(b => {"
       " if (!document.querySelector('ytcp-dialog, tp-yt-paper-dialog[aria-hidden=\"false\"]')) b.remove(); })"
   )
   ```

2. **Upload Dialog `#toggle-button` Collision:**
   Never match `#toggle-button` globally inside Studio — the left sidebar hamburger also has `id="toggle-button"`. Always scope inside `ytcp-uploads-dialog` and match visible `Show more` text (`StudioSelectors.SHOW_MORE`).

3. **Dropdown Menu Leakage (`tp-yt-paper-item:has-text(...)`):**
   Closed `<tp-yt-paper-menu>` menus stay mounted in the DOM. Always filter `:visible`:
   ```python
   opt = pg.locator(f"tp-yt-paper-item:visible:has-text('{target_lang}')").first
   ```

4. **Home Tab Switch `aria-label` Mutates On Toggle:**
   When `Show Home tab.` turns ON, Studio immediately flips its `aria-label` to `Hide Home tab.`. Always match `[aria-label*='Home tab']` (`StudioSelectors.HOME_TAB_TOGGLE`) and read `aria-checked`.

5. **File Input Index Order on `/editing/profile`:**
   Do not hardcode input indices blind; inspect surrounding container text:
   - `input[type='file']` matching `"2048"` / `"banner"` -> Banner (`2560x1440`)
   - `input[type='file']` matching `"98"` / `"picture"` -> Avatar (`800x800`)
   - `input[type='file']` matching `"150"` / `"watermark"` -> Video watermark (`150x150`)

6. **Category Unlocks `Game title (optional)`:**
   `input[aria-label='Game title (optional)']` is absent until `Category` is switched to `Gaming`. Select `Gaming`, wait `SCROLL_SETTLE_MS`, then type and pick from autocomplete.

7. **Brand Account vs. Personal Profile on `www.youtube.com`:**
   Studio edits the Brand Channel while `www.youtube.com` may still be signed into your personal profile. Inspect `#avatar-btn` -> menu text and click `Switch account` if needed before commenting (`_ensure_www_channel_identity()`).

8. **SPA Stall Navigating Studio -> Watch Page:**
   Navigating directly from a completed `ytcp-uploads-dialog` tab to `youtube.com/watch?v=...` can hang on Studio SPA hooks. Always open a fresh `pg.context.new_page()` for comment posting.

9. **Chrome Tab Leak Protection:**
   Stale Studio tabs consume heavy RAM and eventually stall `connect_over_cdp()`. Wrap every `ctx.new_page()` in `try ... finally: await pg.close()`.
