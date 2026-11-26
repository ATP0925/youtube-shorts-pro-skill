# Editing Tools & Automation Pipeline

> The right tool for the right job: CapCut for manual creativity, FFmpeg for backend muscle, Remotion for programmatic scale.

---

## Tool Comparison Matrix

| Criteria | CapCut | FFmpeg + Whisper | Remotion | DaVinci Resolve | After Effects |
|----------|--------|-----------------|----------|----------------|--------------|
| **Target User** | Creators / Editors | Backend Engineers | React Developers | Pro Editors | Motion Designers |
| **Subtitle Gen** | Native 1-click AI | External (Whisper → SRT/ASS) | Built-in `@remotion/captions` | Fairlight + plugins | SRT import |
| **Styling** | Rich preset gallery | Unlimited via ASS | Unlimited (HTML/CSS/React) | Good | Unlimited |
| **Automation** | Manual / app-based | Fully scriptable CLI | Fully programmatic | Manual | Manual + scripts |
| **Batch Processing** | ✗ | ✓ (best) | ✓ | ✗ | ✓ (via ExtendScript) |
| **Cost** | Free (Pro optional) | Free & open source | Free (self-host) | Free (Fusion) | Subscription |
| **Platform** | Win/Mac/Mobile/Web | All | All (Node.js) | Win/Mac/Linux | Win/Mac |
| **Best For** | Quick viral edits | Pipeline backend | SaaS/batch templates | Color grading | Complex VFX |

---

## 1. FFmpeg — The Backend Engine

FFmpeg is the backbone of any automated video pipeline. It handles all encoding, filtering, and subtitle burning.

### 1.1 Essential Commands for Shorts

#### Vertical Video Conversion (Blur Background)
```bash
ffmpeg -i input.mp4 -filter_complex "
[0:v]split=2[bg][fg];
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=r=40:p=3[bg_blurred];
[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg_scaled];
[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2[outv]" \
-map "[outv]" -map 0:a output_vertical.mp4
```

#### Audio Normalization to -14 LUFS (Broadcast Standard)
```bash
ffmpeg -i input.mp4 -af "loudnorm=I=-14:TP=-2:LRA=7" -c:v copy output_normalized.mp4
```

#### Speed Ramp (Normal → 2× Fast → Slow-Mo)
```bash
ffmpeg -i input.mp4 -filter_complex "
[0:v]trim=end=5,setpts=PTS-STARTPTS[v1];
[0:v]trim=start=5:end=10,setpts=0.5*(PTS-STARTPTS)[v2];
[0:v]trim=start=10,setpts=2.0*(PTS-STARTPTS)[v3];
[v1][v2][v3]concat=n=3:v=1:a=0[outv]" \
-map "[outv]" output_ramp.mp4
```

#### Ken Burns Zoom on Static Image (5s)
```bash
ffmpeg -loop 1 -i image.jpg -t 5 -filter_complex "
scale=8000:-1,
zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1080x1920:fps=25,
format=yuv420p" output_kenburns.mp4
```

#### Overlay Watermark/Logo with Timed Appearance
```bash
ffmpeg -i video.mp4 -i logo.png -filter_complex "
[1:v]scale=150:-1[wm];
[0:v][wm]overlay=x=50:y=H-h-50:enable='between(t,2,7)'[outv]" \
-map "[outv]" -map 0:a output_overlay.mp4
```

#### Burn ASS Subtitles into Video
```bash
ffmpeg -i input.mp4 -vf "ass=captions.ass" -c:a copy output_subtitled.mp4
```

### 1.2 Pro ASS Subtitle Template (Viral Style)

```ass
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Style: ViralPop,Montserrat,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,250,1
Style: ViralHighlight,Montserrat,72,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,250,1

[Events]
; Normal word
Dialogue: 0,00:00:01.00,00:00:01.50,ViralPop,,0,0,0,,{\fad(100,100)\fscx90\fscy90\t(0,200,\fscx100\fscy100)}This
; Keyword highlight (yellow)
Dialogue: 0,00:00:01.50,00:00:02.00,ViralHighlight,,0,0,0,,{\fad(100,100)\fscx95\fscy95\t(0,200,\fscx105\fscy105)}FASTEST
; Normal word
Dialogue: 0,00:00:02.00,00:00:02.50,ViralPop,,0,0,0,,{\fad(100,100)}car
```

**Key ASS Override Tags:**
| Tag | Effect |
|-----|--------|
| `\fad(in,out)` | Fade in/out in milliseconds |
| `\fscx` / `\fscy` | Scale X/Y (100 = normal) |
| `\t(start,end,...)` | Animate tag change over time (pop-in) |
| `\c&H00FFFF&` | Change text color (BGR hex) |
| `\bord4` | Outline thickness |
| `\shad2` | Shadow distance |
| `\pos(x,y)` | Absolute position |
| `\an2` | Alignment (2 = bottom center) |

---

## 2. Whisper AI — Transcription Engine

OpenAI's Whisper generates accurate time-coded subtitles from audio.

### 2.1 Basic SRT Generation
```bash
whisper input.mp4 --model medium --language English --output_format srt --output_dir ./subs/
```

### 2.2 Word-Level Timestamps (for word-by-word captions)
```bash
whisper input.mp4 --model medium --word_timestamps True --output_format json --output_dir ./subs/
```

### 2.3 Pipeline Integration Pattern
```
Video → Whisper (transcribe) → JSON/SRT → Python (style/format) → ASS file → FFmpeg (burn in)
```

---

## 3. CapCut — Manual Viral Editing

CapCut is the go-to tool for creators who edit manually. Key features:

### 3.1 Why CapCut Dominates
- **1-click Auto Captions** with animated word-by-word highlight templates
- Pre-built "Hormozi-style" caption presets (Pop, Neon, Karaoke, Bounce)
- Text-based editing: delete a word in transcript → cuts the video audio
- Trending sound/music library integrated with TikTok/Reels charts
- Free on mobile, desktop, and web

### 3.2 CapCut Viral Caption Settings
| Setting | Value |
|---------|-------|
| Font | Montserrat / Impact / Bebas Neue (bold sans-serif) |
| Size | 48-72pt (mobile-readable) |
| Highlight Color | Electric Yellow `#FFFF00` or Neon Green `#00FF00` |
| Base Color | White `#FFFFFF` |
| Outline | Black, 3-4px thickness |
| Shadow | Dark, 2px offset |
| Animation | "Pop" or "Scale" (word-by-word) |
| Position | Center-bottom (above platform UI zone) |

### 3.3 When to Use CapCut vs. FFmpeg
| Scenario | Use |
|----------|-----|
| One-off creative edit | CapCut |
| Batch processing 50+ videos | FFmpeg |
| Automated daily pipeline | FFmpeg + Whisper |
| Custom animated templates | CapCut or After Effects |
| Programmatic SaaS product | Remotion |

---

## 4. Remotion — Programmatic Video Generation

Remotion lets you write videos as React components. Ideal for template-based automation at scale.

### 4.1 Key Packages
| Package | Purpose |
|---------|---------|
| `@remotion/captions` | Parse and render time-coded captions |
| `@remotion/whisper` | Local transcription via WebGPU |
| `@remotion/player` | Preview in browser |
| `@remotion/lambda` | Serverless rendering on AWS |

### 4.2 Subtitle Component Pattern
```tsx
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { useCaptions } from '@remotion/captions';

export const ViralCaptions: React.FC<{src: string}> = ({src}) => {
  const frame = useCurrentFrame();
  const { words } = useCaptions({ src });
  const current = words.find(w => frame >= w.startFrame && frame <= w.endFrame);

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      {current && (
        <div style={{
          fontSize: 72,
          fontWeight: 900,
          fontFamily: 'Montserrat',
          color: current.isKeyword ? '#FFFF00' : '#FFFFFF',
          textShadow: '3px 3px 6px rgba(0,0,0,0.8)',
          WebkitTextStroke: '2px black',
        }}>
          {current.text}
        </div>
      )}
    </AbsoluteFill>
  );
};
```

---

## 5. Sound Design Layer

### 5.1 Sound Effect Categories for Gaming Shorts
| Category | When to Use | Example |
|----------|-------------|---------|
| **Whoosh** | Camera whip, speed transition | Bass-boosted swoosh |
| **Impact** | Car crash, explosion, landing | Sub-bass thud + metallic crunch |
| **Riser** | Building tension before reveal | Ascending synth tone |
| **Blip/Click** | Text pop-in, stat reveal | Digital blip |
| **Drop** | Beat drop, slow-mo moment | 808 bass + reverb hit |
| **Silence** | Before punchline/reveal | 200ms of complete quiet |
| **Engine Rev** | Speed approach, car showcase | Leave original game audio |

### 5.2 Audio Ducking Pattern
```
Background Music:  ████████▁▁▁████████▁▁▁████████
Voiceover/SFX:              ███           ███
                    ↑ duck music when SFX plays, raise back up
```

### 5.3 FFmpeg Audio Mix Command
```bash
ffmpeg -i video.mp4 -i music.mp3 -filter_complex "
[1:a]volume=0.15[music];
[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[audio]" \
-map 0:v -map "[audio]" output_mixed.mp4
```

---

## 6. Complete Automated Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    VIRAL SHORTS PIPELINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. RAW CLIP (Rockstar Editor / Screen Capture)             │
│      ↓                                                      │
│  2. WHISPER AI → Word-level SRT/JSON transcript             │
│      ↓                                                      │
│  3. PYTHON STYLER → ASS subtitle file (viral formatting)    │
│      ↓                                                      │
│  4. FFMPEG MASTER FILTER:                                   │
│      • Vertical 1080×1920 conversion                        │
│      • Speed ramp at action peaks                           │
│      • Burn ASS subtitles                                   │
│      • Audio normalization (-14 LUFS)                       │
│      • Mix background music (ducked)                        │
│      • Overlay watermark/logo                               │
│      ↓                                                      │
│  5. MEDIA VALIDATOR → Resolution / Duration / Loudness      │
│      ↓                                                      │
│  6. CATALOG ENTRY → Title, Tags, Playlist, Game Title       │
│      ↓                                                      │
│  7. CDP UPLOADER → YouTube Studio / Instagram               │
│      ↓                                                      │
│  8. POST-PUBLISH → Owner CTA Comment + Analytics Scrape     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Free SFX & Music Sources

| Source | Type | License |
|--------|------|---------|
| Pixabay | SFX + Music | Royalty-free, no attribution |
| Freesound.org | SFX | Creative Commons (check per file) |
| YouTube Audio Library | Music + SFX | Free for YouTube creators |
| Uppbeat | Music | Free tier with attribution |
| Epidemic Sound | Music + SFX | Subscription, claim-safe |
| Artlist | Music + SFX | Subscription, claim-safe |
| CinePacks | SFX bundles | Paid, one-time purchase |
