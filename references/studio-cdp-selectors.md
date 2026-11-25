# YouTube Studio & Watch DOM Gotchas (Hard-Won Engineering Notes)

1. **Polymer Backdrop Interception (`<tp-yt-iron-overlay-backdrop class="opened">`):**
   Closing a modal or switching tabs quickly can leave an overlay backdrop open that blocks clicking left-nav `#settings-item`. Always click visible `Got it`/`Dismiss`/`Close` buttons, press `Escape`, and remove orphaned backdrops if no dialog remains visible.

2. **Upload Dialog `#toggle-button` Collision:**
   Never match `#toggle-button` globally inside Studio! The left navigation collapse hamburger also uses `id="toggle-button"`. Always scope strictly inside `ytcp-uploads-dialog` + `:visible:has-text('Show more')`.

3. **Dropdown Menu Leakage (`tp-yt-paper-item:has-text(...)`):**
   Closed YouTube Studio `<tp-yt-paper-menu>` instances stay mounted in the DOM. Always filter `:visible` when picking dropdown items (`tp-yt-paper-item:visible:has-text('English (United States)')`).

4. **Home Tab Switch `aria-label` Flips On Toggle:**
   When `Show Home tab.` is turned ON, YouTube Studio immediately mutates its `aria-label` to `Hide Home tab.`. Always match `[aria-label*='Home tab']` instead of `'Show Home tab'`.

5. **File Input Index Order on `/editing/profile`:**
   - `input[type='file']` #0 = **Banner image** (`>= 2048x1152`)
   - `input[type='file']` #1 = **Profile picture** (`>= 98x98`)
   - `input[type='file']` #2 = **Video watermark** (`150x150`)
   Always verify by inspecting surrounding container text rather than assuming index order across Studio versions.

6. **Category Unlocks `Game title (optional)`:**
   `input[aria-label='Game title (optional)']` does NOT exist in DOM if the video's Category is `People & blogs` or `None`. Ensure `#category ytcp-text-dropdown-trigger` -> `Gaming` first, wait `~1.2s`, then type the game title and select the autocomplete item.

7. **Brand Account vs. Personal Profile on `www.youtube.com`:**
   Your Studio session may edit Brand Channel `Vice City Vault` while `www.youtube.com` still defaults to your personal Google profile! Before posting an Owner Comment, inspect `#avatar-btn` popup and use `Switch account` if needed.

8. **SPA Stall Navigating Studio -> Watch Page:**
   Navigating directly from a just-finished `ytcp-uploads-dialog` page to `youtube.com/watch?v=...` in the same tab can stall on Studio SPA hooks. Open a fresh clean `ctx.new_page()` for commenting and close it cleanly in `finally:`.

9. **Chrome Tab Leak Protection:**
   If CDP scripts open `ctx.new_page()` and crash without closing them, stale heavy Studio tabs exhaust browser memory and make `connect_over_cdp()` time out. Always wrap `ctx.new_page()` in `try...finally: await pg.close()` and use `timeout=30000`.
