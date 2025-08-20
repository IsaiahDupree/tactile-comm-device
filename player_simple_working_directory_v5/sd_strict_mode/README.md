# Strict-Mode SD Card Structure

This directory contains the **strict-mode** SD card layout for the tactile communication device. This structure enforces playlist-driven audio playback with complete hardware-software decoupling.

## 🎯 Key Benefits

- **Hardware Independence**: Change GPIO pins by updating `buttons.csv` only
- **Playlist Control**: Audio order strictly enforced by M3U playlists
- **Desktop App Ready**: Standard file formats for cross-platform tools
- **Atomic Updates**: Safe staging/rollback mechanism for content updates
- **Future Proof**: Scales to unlimited buttons and audio content

## 📁 Directory Structure

```
/config/
  mode.cfg                  # Global flags (strict on) + priority
  buttons.csv               # Physical input → logical KEY mapping

/mappings/
  playlists/
    A_human.m3u            # Human recordings for A button
    A_generated.m3u        # TTS audio for A button
    PERIOD_human.m3u       # Human recordings for PERIOD button
    PERIOD_generated.m3u   # TTS audio for PERIOD button
    ...                    # One or both per KEY; absent = bank unavailable

/audio/
  human/
    A/001.mp3 002.mp3 ...  # Human recordings by KEY
    PERIOD/001.mp3 ...
    ...
  generated/
    A/001.mp3 002.mp3 ...  # TTS audio by KEY
    PERIOD/001.mp3 ...
    SYSTEM/001.mp3 ...     # System announcements
    ...

/state/
  cursors.json             # Optional last-played indices per KEY & bank

/_staging/                 # Used only during desktop updates (atomic swap)
/_rollback/                # Last good version (optional)
/manifest.json             # Optional summary (schema + versions) for desktop app
```

## ⚙️ Configuration Files

### `/config/mode.cfg`
Global system settings:
```
PRIORITY=HUMAN_FIRST        # or GENERATED_FIRST
STRICT_PLAYLISTS=1          # strict ON: playlists required; no folder scanning
```

### `/config/buttons.csv`
Physical hardware to logical key mapping:
```
#INPUT,KEY
pcf0:00,A                  # PCF8575 expander 0, pin 0 → A key
pcf0:15,PERIOD             # PCF8575 expander 0, pin 15 → PERIOD key
pcf1:03,WATER              # PCF8575 expander 1, pin 3 → WATER key
gpio:8,BACK                # Direct GPIO pin 8 → BACK key
```

## 🎵 Playlist System

### Format Rules
- **UTF-8 encoding**, **LF newlines**, **no BOM**
- One audio file path per line, **relative to SD root**
- Lines starting with `#` are comments (ignored)
- Paths use **POSIX format** (`/`) even on Windows

### Priority System
- **HUMAN_FIRST**: Try `<KEY>_human.m3u`, fallback to `<KEY>_generated.m3u`
- **GENERATED_FIRST**: Try `<KEY>_generated.m3u`, fallback to `<KEY>_human.m3u`
- **Strict Mode**: Missing playlist = bank unavailable (no folder scanning)

### Multi-Press Behavior
- Within 1000ms: Press count advances through chosen bank playlist
- Wraps to beginning at end of playlist
- Triple-press PERIOD button toggles priority mode globally

## 📋 Button Mapping Reference

Based on your calibration session:

| Hardware Index | PCF Input | Key Label |
|----------------|-----------|-----------|
| 0 | pcf0:00 | YES |
| 1 | pcf0:01 | SHIFT |
| 2 | pcf0:02 | K |
| 3 | pcf0:03 | A |
| 5 | pcf0:05 | P |
| 6 | pcf0:06 | C |
| 7 | pcf0:07 | R |
| 8 | pcf0:08 | I |
| 9 | pcf0:09 | J |
| 10 | pcf0:10 | Q |
| 11 | pcf0:11 | W |
| 13 | pcf0:13 | V |
| 14 | pcf0:14 | X |
| 15 | pcf0:15 | PERIOD |
| 16 | pcf1:00 | N |
| 17 | pcf1:01 | G |
| 18 | pcf1:02 | F |
| 19 | pcf1:03 | M |
| 20 | pcf1:04 | WATER |
| 21 | pcf1:05 | U |
| 22 | pcf1:06 | T |
| 23 | pcf1:07 | L |
| 24 | pcf1:08 | E |
| 25 | pcf1:09 | NO |
| 27 | pcf1:11 | SPACE |
| 28 | pcf1:12 | Z |
| 29 | pcf1:13 | S |
| 30 | pcf1:14 | D |
| 31 | pcf1:15 | Y |
| 33 | pcf2:01 | O |
| 34 | pcf2:02 | B |
| 35 | pcf2:03 | H |

## 🔧 Setup Instructions

1. **Copy Structure**: Copy this entire `sd_strict_mode` folder to your SD card root
2. **Add Audio Files**: Place your MP3 files in the appropriate `/audio/human/` and `/audio/generated/` folders
3. **Update Playlists**: Edit the M3U files to reference your actual audio files
4. **Test Configuration**: Use firmware serial commands to verify setup

## 🖥️ Desktop App Integration

This structure is designed for seamless desktop app integration:

- **Standard M3U playlists** work with any audio management tool
- **Cross-platform file paths** and UTF-8 encoding
- **Atomic updates** via `/_staging/` and `/_rollback/` directories
- **Version tracking** via `manifest.json`
- **State persistence** for resuming playback positions

## ✅ Validation Checklist

- [ ] `mode.cfg` exists with `STRICT_PLAYLISTS=1`
- [ ] Every KEY in `buttons.csv` has at least one playlist file
- [ ] Every M3U entry points to a real audio file
- [ ] All audio files are in correct bank directories (`/audio/human/` or `/audio/generated/`)
- [ ] No audio files referenced from outside `/audio/` structure
- [ ] Reserved directories `/_staging/` and `/_rollback/` exist but are empty
- [ ] Playlist order is the **only** playback order (no directory scanning)

## 🚀 Next Steps

1. **Generate Missing Playlists**: Run the playlist generator script for all remaining keys
2. **Populate Audio Files**: Add your recorded and TTS audio files
3. **Test Firmware**: Upload to device and test button mappings
4. **Desktop Integration**: Build desktop app using this structure as the contract
