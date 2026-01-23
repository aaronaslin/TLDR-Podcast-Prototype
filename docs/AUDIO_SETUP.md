# Audio Enhancement Setup Guide

## Quick Setup

Place your audio files in the `audio/` directory, then update `.env` to enable features.

## Features Ready

### 1. **Voice Speed & Pitch**
Already active! Adjust in `.env`:
```bash
EDGE_TTS_RATE=+15%      # -50% to +100% (current: 15% faster)
EDGE_TTS_PITCH=+0Hz     # ±20Hz typical (e.g., +5Hz, -10Hz)
```

### 2. **Intro Music with Lead-in**
Uncomment in `.env` when ready:
```bash
INTRO_MUSIC_FILE=/Users/aaslin/Documents/GitHub/TLDR Podcast Prototype/audio/intro.mp3
INTRO_MUSIC_LEAD_IN=2        # Seconds of music-only intro
INTRO_MUSIC_VOLUME=0.5       # 0.0 to 1.0 (50% = background level)
```

**How it works:**
- Music plays solo for 2 seconds (configurable lead-in)
- Then continues as background during voice
- Ducking automatically reduces music volume during speech (if enabled)

### 3. **Audio Ducking (Sidechain-style)**
Already enabled! The music automatically gets quieter when voice plays.
```bash
ENABLE_DUCKING=true          # Toggle on/off
DUCKED_VOLUME=0.25           # Music volume during voice (25% of original)
```

### 4. **Outro Music**
Uncomment in `.env` when ready:
```bash
OUTRO_MUSIC_FILE=/Users/aaslin/Documents/GitHub/TLDR Podcast Prototype/audio/outro.mp3
OUTRO_MUSIC_DURATION=5       # Seconds
OUTRO_MUSIC_VOLUME=0.7       # 0.0 to 1.0
```

Auto-fades in (0.5s) and out (1.5s) for smooth ending.

### 5. **Section Chimes**
Uncomment in `.env` when ready:
```bash
SECTION_CHIME_FILE=/Users/aaslin/Documents/GitHub/TLDR Podcast Prototype/audio/chime.mp3
SECTION_CHIME_VOLUME=0.6     # 0.0 to 1.0
```

Chimes play at natural section breaks in the content.

## Audio File Recommendations

### Intro/Outro Music
- **Format:** MP3, WAV, or OGG
- **Length:** 10-30 seconds (will be trimmed automatically)
- **Style:** Tech news intro, corporate, ambient
- **Volume:** Normalized to -14 LUFS or similar

### Section Chimes
- **Format:** MP3, WAV, or OGG
- **Length:** 0.5-2 seconds
- **Examples:** Bell, ding, whoosh, transition sound

## Testing

Run the pipeline without music first to verify voice settings:
```bash
python3 main.py
```

Then add music files and uncomment settings to test enhancements.

## Volume Guidelines

| Setting | Value | Effect |
|---------|-------|--------|
| 1.0 | 100% | Full volume (may overpower voice) |
| 0.7 | 70% | Strong presence (good for outro) |
| 0.5 | 50% | Background level (good for intro music) |
| 0.25 | 25% | Ducked/quiet (automatic during voice) |
| 0.1 | 10% | Very subtle |

## Advanced Tips

**Ducking Intensity:** Lower `DUCKED_VOLUME` for more dramatic sidechain effect.

**Voice Speed:** For longer episodes, try `+20%` or `+25%` for faster delivery.

**Pitch:** Subtle adjustments (±3Hz) change warmth; larger changes (±10Hz) alter character significantly.

**Lead-in Duration:** Extend to 3-5 seconds for a more cinematic opening.
