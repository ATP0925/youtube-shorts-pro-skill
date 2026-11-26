# Thumbnail & Cover Frame Optimization

> The cover frame is your billboard. It decides whether a viewer taps your Short from search, channel pages, and suggested shelves.

---

## 1. Where Cover Frames Appear

| Surface | Aspect Ratio | Size | Notes |
|---------|-------------|------|-------|
| Shorts Swipe Feed | Full 9:16 | 1080×1920 | First frame plays automatically — no thumbnail shown |
| Channel Page Grid | ~4:5 crop | Small tile | Cover is cropped vertically — keep content centered |
| YouTube Search | ~4:5 crop | Medium tile | Text must be large enough to read at this size |
| Suggested Shorts Shelf | ~4:5 crop | Small tile | Competing with 4-6 other thumbnails |
| Instagram Profile Grid | 1:1 crop | Small tile | Only the center square is shown |

> **Key Insight:** The Shorts swipe feed auto-plays the first frame, so the cover frame matters most for discovery OUTSIDE the feed (search, channel page, shelves).

---

## 2. Cover Frame Design Rules

### 2.1 The 3-Word Maximum Rule
Viewers glance at Shorts covers in a fraction of a second. Long sentences fail.

```
✓ "FASTEST CAR"           → 2 words, instant curiosity
✓ "He Actually Won"       → 3 words, story hook
✓ "SECRET LOCATION"       → 2 words, forbidden knowledge
✗ "Watch Me Find The Rarest Car In GTA 6 Vice City"  → too long
```

### 2.2 Single Focal Point
One clear subject per cover — a car, an explosion, a character. Never clutter.

```
✓ One supercar centered, text above
✗ 4 small screenshots collaged together
```

### 2.3 High Contrast & Massive Font
Covers display very small on mobile grids. Tiny text is invisible.

| Element | Specification |
|---------|--------------|
| **Font** | Bold, heavy sans-serif (Montserrat, Impact, Bebas Neue) |
| **Font Size** | Minimum 72pt at 1080×1920 canvas |
| **Text Color** | White or Electric Yellow on dark backgrounds |
| **Outline** | Thick dark outline (3-5px) OR solid background box |
| **Shadow** | Dark drop shadow for depth |
| **Readability** | Must be legible at 150×200px thumbnail size |

### 2.4 Safe Zone Placement
Keep all important content (text + subject) within the center safe zone to avoid platform UI clipping.

```
┌──────────────────────────┐
│   ░░░ TOP UNSAFE ░░░░░░ │  ← Channel name, timestamps
│                          │
│   ┌──────────────────┐   │
│   │                  │   │
│   │   SAFE ZONE      │   │
│   │   (Text + Face)  │   │
│   │                  │   │
│   │   920 × 1200px   │   │
│   │                  │   │
│   └──────────────────┘   │
│                          │
│   ░░░ BOTTOM UNSAFE ░░░ │  ← Like/comment buttons, caption text
│   ░░ RIGHT UNSAFE ░░░░░ │  ← Share, subscribe overlay
└──────────────────────────┘
```

**Pixel Margins (1080×1920):**
| Edge | Unsafe Zone | Reason |
|------|------------|--------|
| Top | 0-200px | Channel name, back button |
| Bottom | 1570-1920px | Caption, music ticker, like/comment/share buttons |
| Right | 920-1080px | Like, comment, share, subscribe vertical strip |
| Left | 0-80px | Minimal, but avoid edges |

---

## 3. First Frame Alignment

### 3.1 Cover = First Frame Rule
The cover and the very first frame of the video should match seamlessly.

**Why:** If a viewer finds your Short via search/channel page and the first frame doesn't match what they expected from the cover, they feel deceived and swipe away immediately.

### 3.2 Anti-Patterns
| Anti-Pattern | Impact |
|-------------|--------|
| Black/fade-in opening | Cover looks broken; instant swipe |
| Logo/brand intro first | Wastes 2-3s; doesn't match cover |
| Random mid-video frame as cover | Disorienting for the viewer |
| All-text cover with no visual | Looks like clickbait, not content |

### 3.3 Pro Technique: Title Card as Frame 1
Design the cover text overlay as the very first frame of your video timeline:
1. Create the title card in your editor
2. Place it as the first 0.5-1 second of the video
3. Transition immediately into the action
4. Select this exact frame as the cover in YouTube Studio

---

## 4. Gaming Channel Cover Strategies

### 4.1 Effective Cover Formats for GTA Gaming
| Format | Example | Why It Works |
|--------|---------|-------------|
| **Action Freeze-Frame** | Car mid-drift with motion blur | Shows intensity, promises action |
| **Before/After Split** | Stock car → modified beast | Transformation curiosity |
| **Reaction Face + Game** | Shocked expression + game screenshot | Emotional hook |
| **Stat/Number Overlay** | "0 to 200mph" on car image | Quantified promise |
| **Mystery/Hidden** | Blurred/obscured discovery + "???" | Curiosity gap |

### 4.2 Color Psychology for Gaming
| Color | Emotion | Use Case |
|-------|---------|----------|
| Red | Urgency, danger, action | Crashes, fights, warnings |
| Electric Yellow | Energy, speed, attention | Speed runs, records |
| Neon Green | Discovery, money, success | Finds, earnings, wins |
| Blue | Cool, trust, tech | Reviews, comparisons |
| Orange | Fun, excitement | Stunts, challenges |

---

## 5. FFmpeg Cover Frame Extraction

### Extract Best Frame at Specific Timestamp
```bash
ffmpeg -ss 00:00:02.500 -i input.mp4 -frames:v 1 -q:v 2 cover_frame.jpg
```

### Extract Multiple Candidate Frames
```bash
ffmpeg -i input.mp4 -vf "select='gt(scene,0.3)',scale=1080:1920" \
  -vsync vfr -frames:v 5 cover_%02d.jpg
```
This extracts frames where scene change is detected (most visually interesting moments).

### Add Text Overlay to Extracted Frame
```bash
ffmpeg -i cover_frame.jpg -vf "
drawtext=text='FASTEST CAR':fontfile=Montserrat-Bold.ttf:
fontsize=90:fontcolor=white:borderw=5:bordercolor=black:
x=(w-text_w)/2:y=h*0.35" cover_with_text.jpg
```

---

## 6. Instagram Profile Grid Optimization

Instagram Reels appear as 1:1 squares on the profile grid. Your vertical cover gets center-cropped.

### Safe Zone for Instagram Grid
```
┌──────────────────────────┐
│                          │
│   ░░░░ CROPPED ░░░░░░░ │  ← Top 420px hidden on grid
│                          │
│   ┌──────────────────┐   │
│   │  VISIBLE ON GRID │   │
│   │  (Center 1080²)  │   │
│   │  Put text here   │   │
│   └──────────────────┘   │
│                          │
│   ░░░░ CROPPED ░░░░░░░ │  ← Bottom 420px hidden on grid
│                          │
└──────────────────────────┘
```

**Dual-Safe Cover Design:** Place your 2-3 word text overlay in the absolute vertical center (y = 850-1070px range at 1920 height) to be visible on BOTH YouTube and Instagram grids.

---

## 7. Cover Frame Quality Checklist

- [ ] **1 focal point** — one clear car/character/object
- [ ] **Max 3 words** of large, bold, high-contrast text
- [ ] **Centered safely** — away from all platform UI zones
- [ ] **Matches first frame** — seamless visual continuity
- [ ] **No black/blank** — vibrant, saturated, action-filled
- [ ] **Legible at 150px** — text readable at tiny thumbnail size
- [ ] **No watermarks** from other platforms
- [ ] **1080×1920** resolution (never lower)
- [ ] **Consistent style** across all Shorts (brand recognition)
