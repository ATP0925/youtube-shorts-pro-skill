"""
Parameterized Pro YouTube Channel Branding Asset Generator.

Generates crisp, production-quality branding assets:
  1. **800×800** circular-safe Neon Gaming Emblem Avatar
  2. **2560×1440** Banner strictly inside the 1546×423 safe zone
  3. **150×150** high-contrast Subscribe Video Watermark
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logger import get_logger

log = get_logger(__name__)

__all__ = ["build_pro_avatar", "build_pro_banner", "build_pro_watermark"]


# ── Font loading ────────────────────────────────────────────────────────

def _load_font(size: int, bold: bool = True):
    """Load the best available system font, with cross-platform fallbacks."""
    try:
        from PIL import ImageFont
    except ImportError:
        log.error("Pillow not installed. Run: pip install Pillow>=10.0")
        sys.exit(1)

    candidates = [
        # Windows
        r"C:\Windows\Fonts\seguibl.ttf" if bold else r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        # macOS
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFPro.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    log.warning("No system font found; falling back to Pillow default bitmap font")
    return ImageFont.load_default()


# ── Avatar (800×800) ────────────────────────────────────────────────────

def build_pro_avatar(
    out_path: Path,
    badge: str = "VI",
    label: str = "CREATOR",
    pill: str = "4K SHORTS",
) -> None:
    """Generate an 800×800 neon gaming emblem avatar.

    Args:
        out_path: Destination file path.
        badge: Center monogram text (1-3 chars recommended).
        label: Sub-text below the monogram.
        pill: Text inside the pill badge at the bottom.
    """
    from PIL import Image, ImageDraw

    size = 800
    img = Image.new("RGBA", (size, size), (12, 7, 28, 255))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(size):
        t = y / size
        r = int(16 + 40 * math.sin(t * math.pi))
        g = int(8 + 12 * (1 - t))
        b = int(42 + 35 * (1 - t))
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Concentric rings
    draw.ellipse([24, 24, 776, 776], outline=(0, 235, 255, 255), width=16)
    draw.ellipse([46, 46, 754, 754], outline=(255, 45, 145, 255), width=10)
    draw.ellipse([66, 66, 734, 734], fill=(12, 8, 28, 230), outline=(255, 215, 0, 200), width=3)

    f_badge = _load_font(270 if len(badge) <= 3 else 180, bold=True)
    f_sub = _load_font(50, bold=True)
    f_pill = _load_font(34, bold=False)

    # Chromatic aberration badge
    draw.text((388, 305), badge, font=f_badge, fill=(0, 240, 255), anchor="mm")
    draw.text((412, 315), badge, font=f_badge, fill=(255, 40, 140), anchor="mm")
    draw.text((400, 310), badge, font=f_badge, fill=(255, 255, 255), anchor="mm")

    # Label and pill
    draw.text((400, 520), label[:16], font=f_sub, fill=(255, 215, 0), anchor="mm")
    draw.rounded_rectangle(
        [225, 575, 575, 635], radius=28, fill=(255, 35, 130, 245), outline=(0, 240, 255, 255), width=3,
    )
    draw.text((400, 604), pill[:16], font=f_pill, fill=(255, 255, 255), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, "PNG")
    log.info("Saved Avatar (800×800): %s", out_path)


# ── Palm tree helper ────────────────────────────────────────────────────

def _draw_palm(draw: ImageDraw.ImageDraw, bx: int, by: int, scale: float, flip: int = 1) -> None:
    """Draw a stylized palm tree silhouette on the banner."""
    pts = []
    for i in range(14):
        t = i / 13.0
        px = bx + flip * int(60 * scale * (t ** 1.6))
        py = by - int(360 * scale * t)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        w = max(4, int((16 - i) * scale))
        draw.line([pts[i], pts[i + 1]], fill=(10, 5, 24, 255), width=w)
    top_x, top_y = pts[-1]
    for ang_deg in [-155, -125, -90, -45, -15, 20, 160]:
        rad = math.radians(ang_deg)
        length = 140 * scale
        ex = top_x + int(math.cos(rad) * length)
        ey = top_y + int(math.sin(rad) * length * 0.75 + 25 * scale)
        cx = (top_x + ex) // 2
        cy = min(top_y, ey) - int(28 * scale)
        draw.polygon([(top_x, top_y), (cx, cy), (ex, ey), (cx, cy + int(22 * scale))], fill=(10, 5, 24, 255))


# ── Banner (2560×1440) ──────────────────────────────────────────────────

def build_pro_banner(
    out_path: Path,
    title: str = "YOUR CHANNEL VAULT",
    subtitle: str = "4K CLIPS  |  VIRAL MOMENTS  |  DAILY SHORTS",
    schedule_pill: str = "NEW SHORTS DAILY  |  9 AM & 5 PM EST",
) -> None:
    """Generate a 2560×1440 banner with text in the 1546×423 safe zone.

    Args:
        out_path: Destination file path.
        title: Main title text.
        subtitle: Subtitle below the title.
        schedule_pill: Text inside the schedule pill badge.
    """
    from PIL import Image, ImageDraw

    W, H = 2560, 1440
    canvas = Image.new("RGBA", (W, H), (10, 6, 26, 255))
    draw = ImageDraw.Draw(canvas)

    # Gradient sky
    for y in range(H):
        t = y / H
        if t < 0.58:
            st = t / 0.58
            r, g, b = int(16 + 150 * (st ** 1.4)), int(10 + 35 * (st ** 1.8)), int(48 + 90 * st - 30 * (st ** 2))
        else:
            ot = (t - 0.58) / 0.42
            r, g, b = int(28 - 18 * ot), int(16 + 45 * (1 - ot)), int(75 + 45 * (1 - ot))
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Retro sun
    sun_cx, sun_cy, sun_r = 1280, 740, 340
    sun_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun_layer)
    for y in range(sun_cy - sun_r, sun_cy + sun_r):
        dy = y - sun_cy
        if abs(dy) < sun_r:
            half_w = int(math.sqrt(sun_r * sun_r - dy * dy))
            if dy > 35 and ((dy // 26) % 2 == 1):
                continue
            gt = (y - (sun_cy - sun_r)) / (2 * sun_r)
            col = (255, int(210 - 155 * gt), int(60 + 80 * gt), 220)
            sd.line([(sun_cx - half_w, y), (sun_cx + half_w, y)], fill=col)
    canvas = Image.alpha_composite(canvas, sun_layer)
    draw = ImageDraw.Draw(canvas)

    # Horizon & grid
    horizon_y = 845
    draw.line([(0, horizon_y), (W, horizon_y)], fill=(0, 245, 255, 255), width=6)
    for k in range(-14, 15):
        draw.line([(1280 + k * 70, horizon_y), (1280 + k * 280, H)], fill=(0, 220, 255, 110), width=3)
    for i in range(1, 9):
        gy = horizon_y + int(((i / 8) ** 1.7) * (H - horizon_y))
        draw.line([(0, gy), (W, gy)], fill=(255, 45, 155, 100), width=3)

    # Palm trees
    for bx, sc, fl in [(390, 1.45, 1), (540, 1.05, 1), (2170, 1.45, -1), (2020, 1.05, -1)]:
        _draw_palm(draw, bx, 960 if sc > 1.2 else 935, sc, flip=fl)

    # Center safe-zone glass card
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([590, 540, 1970, 900], radius=38, fill=(10, 6, 26, 228), outline=(255, 45, 145, 255), width=6)
    cd.rounded_rectangle([600, 550, 1960, 890], radius=31, outline=(0, 240, 255, 235), width=3)
    canvas = Image.alpha_composite(canvas, card)
    draw = ImageDraw.Draw(canvas)

    f_title = _load_font(116 if len(title) <= 18 else 92, bold=True)
    f_sub = _load_font(38, bold=False)
    f_pill = _load_font(31, bold=True)

    # Chromatic title
    draw.text((1274, 645), title, font=f_title, fill=(0, 240, 255), anchor="mm")
    draw.text((1286, 653), title, font=f_title, fill=(255, 40, 140), anchor="mm")
    draw.text((1280, 649), title, font=f_title, fill=(255, 255, 255), anchor="mm")
    draw.text((1280, 750), subtitle, font=f_sub, fill=(255, 215, 0), anchor="mm")

    # Schedule pill
    draw.rounded_rectangle(
        [860, 802, 1700, 862], radius=26, fill=(255, 35, 135, 245), outline=(0, 240, 255, 255), width=3,
    )
    draw.text((1280, 831), schedule_pill, font=f_pill, fill=(255, 255, 255), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "PNG")
    log.info("Saved Banner (2560×1440): %s", out_path)


# ── Watermark (150×150) ─────────────────────────────────────────────────

def build_pro_watermark(out_path: Path, badge: str = "VI") -> None:
    """Generate a 150×150 Subscribe watermark badge.

    Args:
        out_path: Destination file path.
        badge: Center monogram text.
    """
    from PIL import Image, ImageDraw

    size = 150
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([6, 6, 144, 144], radius=28, fill=(14, 10, 32, 235), outline=(0, 240, 255, 255), width=4)
    draw.rounded_rectangle([12, 12, 138, 138], radius=22, outline=(255, 45, 145, 220), width=2)

    f_badge = _load_font(56 if len(badge) <= 2 else 42, bold=True)
    f_sub = _load_font(17, bold=True)

    draw.text((73, 52), badge, font=f_badge, fill=(0, 240, 255), anchor="mm")
    draw.text((77, 55), badge, font=f_badge, fill=(255, 40, 140), anchor="mm")
    draw.text((75, 53), badge, font=f_badge, fill=(255, 255, 255), anchor="mm")
    draw.rounded_rectangle(
        [14, 95, 136, 129], radius=12, fill=(255, 24, 58, 255), outline=(255, 255, 255, 230), width=2,
    )
    draw.text((75, 112), "SUBSCRIBE", font=f_sub, fill=(255, 255, 255), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    log.info("Saved Watermark (150×150): %s", out_path)


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point for branding asset generation."""
    parser = argparse.ArgumentParser(description="Generate Pro YouTube Channel Branding Assets")
    parser.add_argument("--badge", default="VI", help="Center monogram (avatar + watermark)")
    parser.add_argument("--title", default="YOUR CHANNEL", help="Channel title for banner")
    parser.add_argument("--label", default="CREATOR", help="Label text below avatar monogram")
    parser.add_argument("--avatar-pill", default="4K SHORTS", help="Bottom pill badge text on avatar")
    parser.add_argument("--subtitle", default="4K CLIPS  |  VIRAL MOMENTS  |  DAILY SHORTS")
    parser.add_argument("--pill", default="NEW SHORTS DAILY  |  9 AM & 5 PM EST")
    parser.add_argument("--out-dir", default="assets", help="Output directory for assets")
    args = parser.parse_args()

    try:
        import PIL  # noqa: F401
    except ImportError:
        log.error("Pillow is required. Install with: pip install Pillow>=10.0")
        sys.exit(1)

    out = Path(args.out_dir)
    build_pro_avatar(
        out / "avatar_800.png",
        badge=args.badge,
        label=args.label.upper(),
        pill=args.avatar_pill.upper(),
    )
    build_pro_banner(
        out / "banner_2560x1440.png",
        title=args.title.upper(),
        subtitle=args.subtitle,
        schedule_pill=args.pill,
    )
    build_pro_watermark(out / "watermark_150.png", badge=args.badge)
    log.info("All 3 branding assets generated in %s/", out)


if __name__ == "__main__":
    main()
