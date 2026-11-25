"""
Centralized constants for youtube-shorts-pro-skill.

All magic numbers, timeouts, thresholds, and DOM selectors live here.
Import specific constants or groups into each module as needed.
"""

from __future__ import annotations

__all__ = [
    "CDP_DEFAULT_URL",
    "CDP_CONNECT_TIMEOUT_MS",
    "CDP_VERSION_ENDPOINT",
    "CDP_HTTP_TIMEOUT_S",
    "PAGE_LOAD_TIMEOUT_MS",
    "PAGE_LOAD_WAIT_UNTIL",
    "STUDIO_SETTLE_MS",
    "UPLOAD_ATTACH_SETTLE_MS",
    "DROPDOWN_SETTLE_MS",
    "MODAL_DISMISS_MS",
    "SCROLL_SETTLE_MS",
    "SHORT_SETTLE_MS",
    "MEDIUM_SETTLE_MS",
    "LONG_SETTLE_MS",
    "STEP_NEXT_SETTLE_MS",
    "SETTINGS_OPEN_SETTLE_MS",
    "GAME_AUTOCOMPLETE_SETTLE_MS",
    "COMMENT_POST_SETTLE_MS",
    "IDENTITY_SWITCH_SETTLE_MS",
    "WATERMARK_ATTACH_SETTLE_MS",
    "SAVE_BUTTON_POLL_S",
    "UPLOAD_CONFIRM_MAX_POLLS",
    "UPLOAD_CONFIRM_POLL_MS",
    "FILE_INPUT_ATTACH_TIMEOUT_MS",
    "TITLE_BOX_TIMEOUT_MS",
    "CREATE_BUTTON_TIMEOUT_MS",
    "UPLOAD_ITEM_TIMEOUT_MS",
    "SHORTS_MAX_DURATION_S",
    "SHORTS_ASPECT_WIDTH",
    "SHORTS_ASPECT_HEIGHT",
    "SHORTS_ASPECT_TOLERANCE",
    "MAX_TITLE_LENGTH",
    "MAX_STUDIO_TITLE_LENGTH",
    "MAX_STUDIO_DESC_LENGTH",
    "MAX_TAGS_STRING_LENGTH",
    "REQUIRED_HASHTAG",
    "LOUDNESS_MIN_DB",
    "LOUDNESS_MAX_DB",
    "LOUDNESS_IDEAL_MIN_DB",
    "LOUDNESS_IDEAL_MAX_DB",
    "FFMPEG_VOLUMEDETECT_TIMEOUT_S",
    "FFPROBE_CHECK_TIMEOUT_S",
    "MAX_COMMENT_THREADS_TO_SCAN",
    "MAX_INBOX_REPLIES_PER_RUN",
    "COMMENT_SPAM_KEYWORDS",
    "DEFAULT_REPLY_TEXT",
    "MAX_ANALYTICS_HISTORY_ENTRIES",
    "DEFAULT_MORNING_WINDOW",
    "DEFAULT_NIGHT_START_HOUR",
    "NIGHT_WINDOW_MINUTE_THRESHOLD",
    "IG_POST_CONFIRM_MAX_POLLS",
    "IG_POST_CONFIRM_POLL_MS",
    "IG_CAPTION_MIN_LENGTH",
    "IG_NEXT_STEP_SETTLE_MS",
    "IG_SUSPENSION_INDICATORS",
    "LOG_DIR_NAME",
    "LOG_FILE_NAME",
    "LOG_MAX_BYTES",
    "LOG_BACKUP_COUNT",
    "LOG_FORMAT",
    "LOG_DATE_FORMAT",
    "AUTH_GATE_URL_PATTERN",
    "AUTH_GATE_BODY_PATTERNS",
    "StudioSelectors",
    "IGSelectors",
]

# ── CDP Connection ──────────────────────────────────────────────────────
CDP_DEFAULT_URL = "http://localhost:9222"
CDP_CONNECT_TIMEOUT_MS = 30_000
CDP_VERSION_ENDPOINT = "/json/version"
CDP_HTTP_TIMEOUT_S = 2.0

# ── Page Navigation & Settling ──────────────────────────────────────────
PAGE_LOAD_TIMEOUT_MS = 45_000
PAGE_LOAD_WAIT_UNTIL = "domcontentloaded"
STUDIO_SETTLE_MS = 4_500            # Wait after navigating to Studio pages
UPLOAD_ATTACH_SETTLE_MS = 5_000     # Wait after attaching file to upload dialog
DROPDOWN_SETTLE_MS = 1_000          # Wait after opening a dropdown
MODAL_DISMISS_MS = 500              # Wait after dismissing a modal/backdrop
SCROLL_SETTLE_MS = 1_200            # Wait between scroll attempts
SHORT_SETTLE_MS = 300               # Micro-wait for DOM mutations
MEDIUM_SETTLE_MS = 700              # Standard post-action wait
LONG_SETTLE_MS = 1_500              # Wait after complex DOM changes
STEP_NEXT_SETTLE_MS = 1_800         # Wait between Upload dialog wizard steps
SETTINGS_OPEN_SETTLE_MS = 2_000     # Wait after clicking Studio Settings
GAME_AUTOCOMPLETE_SETTLE_MS = 2_000 # Wait for Game Title autocomplete results
WATERMARK_ATTACH_SETTLE_MS = 2_500  # Wait for watermark cropper dialog
COMMENT_POST_SETTLE_MS = 3_500      # Wait after submitting an owner comment
IDENTITY_SWITCH_SETTLE_MS = 4_000   # Wait after switching YouTube account
SAVE_BUTTON_POLL_S = 15             # Max seconds to poll Save button

# ── Upload Dialog ───────────────────────────────────────────────────────
UPLOAD_CONFIRM_MAX_POLLS = 30
UPLOAD_CONFIRM_POLL_MS = 2_000
FILE_INPUT_ATTACH_TIMEOUT_MS = 20_000
TITLE_BOX_TIMEOUT_MS = 25_000
CREATE_BUTTON_TIMEOUT_MS = 15_000
UPLOAD_ITEM_TIMEOUT_MS = 10_000

# ── Video Validation ────────────────────────────────────────────────────
SHORTS_MAX_DURATION_S = 60.0
SHORTS_ASPECT_WIDTH = 1080
SHORTS_ASPECT_HEIGHT = 1920
SHORTS_ASPECT_TOLERANCE = 0.01
MAX_TITLE_LENGTH = 60
MAX_STUDIO_TITLE_LENGTH = 100
MAX_STUDIO_DESC_LENGTH = 4_900
MAX_TAGS_STRING_LENGTH = 450
REQUIRED_HASHTAG = "#Shorts"

# ── Audio Loudness (FFmpeg volumedetect) ────────────────────────────────
LOUDNESS_MIN_DB = -38.0        # Hard floor — below this is near-silent
LOUDNESS_MAX_DB = -3.0         # Hard ceiling — above this is clipping
LOUDNESS_IDEAL_MIN_DB = -22.0  # Recommended broadcast floor
LOUDNESS_IDEAL_MAX_DB = -6.0   # Recommended broadcast ceiling
FFMPEG_VOLUMEDETECT_TIMEOUT_S = 25
FFPROBE_CHECK_TIMEOUT_S = 5

# ── Comments ────────────────────────────────────────────────────────────
MAX_COMMENT_THREADS_TO_SCAN = 5
MAX_INBOX_REPLIES_PER_RUN = 3
COMMENT_SPAM_KEYWORDS = ("http://", "https://", "t.me/", "whatsapp", "crypto")
DEFAULT_REPLY_TEXT = "Appreciate the support! Drop what moment you want clipped next!"

# ── Analytics ───────────────────────────────────────────────────────────
MAX_ANALYTICS_HISTORY_ENTRIES = 60

# ── Scheduling ──────────────────────────────────────────────────────────
DEFAULT_MORNING_WINDOW = (18, 21)   # IST hours for US EST morning
DEFAULT_NIGHT_START_HOUR = 21       # IST hour for US night slot
NIGHT_WINDOW_MINUTE_THRESHOLD = 30  # Minutes past hour to start night

# ── Instagram ───────────────────────────────────────────────────────────
IG_POST_CONFIRM_MAX_POLLS = 20
IG_POST_CONFIRM_POLL_MS = 3_000
IG_CAPTION_MIN_LENGTH = 20
IG_NEXT_STEP_SETTLE_MS = 2_500

IG_SUSPENSION_INDICATORS = (
    "suspended your account",
    "account suspended",
    "we suspended",
    "help us confirm that it's you",
    "action blocked",
    "your account has been disabled",
    "we restrict certain activity",
    "confirm your info",
)

# ── Logging ─────────────────────────────────────────────────────────────
LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "yt_pro.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s — %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Google Auth Gate Detection ──────────────────────────────────────────
AUTH_GATE_URL_PATTERN = "accounts.google.com"
AUTH_GATE_BODY_PATTERNS = (
    "verify it's you",
    "verify it\u2019s you",
    "sign in again to continue",
    "enter your password",
    "2-step verification",
    "confirm it's you",
)


# ── Studio DOM Selectors (grouped for maintainability) ──────────────────
class StudioSelectors:
    """YouTube Studio & Watch Polymer DOM selectors — single source of truth."""

    # Navigation
    SETTINGS_ITEM = "#settings-item, tp-yt-paper-icon-item:has-text('Settings')"
    CHANNEL_TAB = "li:has-text('Channel'), tp-yt-paper-item:has-text('Channel')"

    # Backdrops & Modals
    OPENED_BACKDROP = "tp-yt-iron-overlay-backdrop.opened"
    DISMISS_BUTTONS = (
        "ytcp-dialog:visible button:visible:has-text('Got it'), "
        "ytcp-dialog:visible button:visible:has-text('Dismiss'), "
        "tp-yt-paper-dialog:visible button:visible:has-text('Close'), "
        "ytcp-dialog:visible #close-button button:visible"
    )

    # Home Tab
    HOME_TAB_TOGGLE = (
        "tp-yt-paper-toggle-button[aria-label*='Home tab'], "
        "[role='switch'][aria-label*='Home tab']"
    )

    # Upload Dialog
    CREATE_BUTTON = "#create-icon, ytcp-button#create-icon, button[aria-label='Create']"
    UPLOAD_ITEM = "#text-item-0, tp-yt-paper-item:has-text('Upload videos')"
    FILE_INPUT = "input[type='file']"
    TITLE_TEXTBOX = "#title-textarea #textbox, ytcp-social-suggestions-textbox[id='title-textarea'] div#textbox"
    DESC_TEXTBOX = (
        "#description-textarea #textbox, "
        "ytcp-social-suggestions-textbox[id='description-textarea'] div#textbox"
    )
    NOT_MADE_FOR_KIDS = "tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']"
    NEXT_BUTTON = "#next-button"
    DONE_BUTTON = "#done-button"
    PUBLISH_BUTTON = "#publish-button button, #publish-button"
    SAVE_BUTTON = "ytcp-button#save button, ytcp-button#save"
    VIDEO_LINK = "a[href*='youtu.be/'], a[href*='youtube.com/shorts/']"
    SHARE_DIALOG = "ytcp-video-share-dialog, ytcp-uploads-still-processing-dialog, tp-yt-paper-dialog"
    SHARE_CLOSE_BUTTON = "#close-button, ytcp-button:has-text('Close'), button:has-text('Close')"
    UPLOADS_DIALOG = "ytcp-uploads-dialog"

    # Playlists
    PLAYLIST_TRIGGER = "ytcp-video-metadata-playlists ytcp-text-dropdown-trigger"
    PLAYLIST_DIALOG = "tp-yt-paper-dialog:has-text('Done'), ytcp-playlist-dialog:has-text('Done')"
    PLAYLIST_DONE = "button:visible:has-text('Done'), ytcp-button:visible:has-text('Done')"

    # Show More / Category / Language
    SHOW_MORE = "ytcp-button:visible:has-text('Show more'), button:visible:has-text('Show more')"
    CATEGORY_TRIGGER = "#category ytcp-text-dropdown-trigger"
    LANG_DROPDOWN_TEMPLATE = "ytcp-text-dropdown-trigger:has-text('{label}')"
    GAME_TITLE_INPUT = "input[aria-label='Game title (optional)']"
    GAME_AUTOCOMPLETE_OPTION = (
        "tp-yt-paper-item:visible:has-text('{title}'), "
        "ytcp-text-menu tp-yt-paper-item:visible:has-text('{title}'), "
        "[role='option']:visible:has-text('{title}')"
    )
    TAGS_INPUT = "input[aria-label='Tags'], #tags-container input"
    TAGS_CHIPS = "#tags-container ytcp-chip"

    # Altered Content
    ALTERED_NO = "tp-yt-paper-radio-button[name='VIDEO_HAS_ALTERED_CONTENT_NO']"
    ALTERED_YES = "tp-yt-paper-radio-button[name='VIDEO_HAS_ALTERED_CONTENT_YES']"

    # Settings Dialog
    SETTINGS_DIALOG = "ytcp-dialog, ytcp-settings-dialog"
    ADVANCED_TAB = "tp-yt-paper-tab:has-text('Advanced settings'), div[role='tab']:has-text('Advanced')"
    FEATURE_TAB = "tp-yt-paper-tab:has-text('Feature eligibility'), div[role='tab']:has-text('Feature')"
    NOT_FOR_KIDS_CHANNEL = "tp-yt-paper-radio-button:has-text('not Made for Kids')"
    SAVE_SETTINGS = "#save-button button, #save-button"
    CLOSE_SETTINGS = "#close-button button, button:has-text('Close')"

    # Watermark Upload
    WATERMARK_CROP_DONE = (
        "ytcp-image-cropper-dialog:visible #done-button button:visible, "
        "tp-yt-paper-dialog:visible button:visible:has-text('Done'), "
        "ytcp-dialog:visible button:visible:has-text('Done')"
    )
    ENTIRE_VIDEO_RADIO = "tp-yt-paper-radio-button:visible:has-text('Entire video')"

    # Video Rows (Content page)
    VIDEO_ROW = "ytcp-video-row"
    PLAYLIST_METADATA = "ytcp-video-metadata-playlists"

    # Comments (Watch page & Studio Inbox)
    COMMENT_PLACEHOLDER = "#placeholder-area"
    COMMENT_EDITABLE = "#contenteditable-root:visible"
    COMMENT_SUBMIT = "ytd-commentbox #submit-button button:visible, #submit-button button:visible"
    COMMENT_THREADS = "ytd-comment-thread-renderer"
    COMMENT_MENU = "ytd-comment-thread-renderer #action-menu button"
    PIN_ITEM = "tp-yt-paper-item:visible:has-text('Pin'), ytd-menu-service-item-renderer:visible:has-text('Pin')"
    PIN_CONFIRM = "yt-confirm-dialog-renderer #confirm-button button, tp-yt-paper-dialog button:has-text('Pin')"
    SHORTS_COMMENT_BUTTON = "#comments-button button, button[aria-label*='comment' i]"
    INBOX_THREAD = "ytcp-comment-thread"
    INBOX_REPLY_BUTTON = "ytcp-button:has-text('Reply'), button:has-text('Reply')"
    INBOX_REPLY_TEXTBOX = "textarea, div[contenteditable='true']"
    INBOX_REPLY_SUBMIT = "#submit-button button, ytcp-button:has-text('Reply') button"

    # Avatar / Identity
    AVATAR_BUTTON = "#avatar-btn"
    ACCOUNT_MENU_POPUP = "ytd-multi-page-menu-renderer:visible, tp-yt-iron-dropdown:visible"
    SWITCH_ACCOUNT = (
        "tp-yt-compact-link-renderer:visible:has-text('Switch account'), "
        "ytd-compact-link-renderer:visible:has-text('Switch account')"
    )
    ACCOUNT_ITEM_TEMPLATE = "ytd-account-item-renderer:visible:has-text('{name}')"

    # Visibility
    VISIBILITY_RADIO = "tp-yt-paper-radio-button[name='{visibility}']"


class IGSelectors:
    """Instagram Web DOM selectors."""

    NEW_POST = "svg[aria-label='New post'], svg[aria-label='Post'], svg[aria-label='Create']"
    FILE_INPUT_VIDEO = "input[type='file'][accept*='video/mp4']"
    FILE_INPUT_ANY = "input[type='file']"
    DIALOG = "div[role='dialog']"
    OK_BUTTON = "button:has-text('OK'), div[role='button']:has-text('OK')"
    NEXT_BUTTON = "div[role='button']:has-text('Next'), button:has-text('Next')"
    CAPTION_BOX = "div[aria-label*='caption' i], div[role='textbox'], div[contenteditable='true']"
    SHARE_BUTTON = "div[role='button'], button"
