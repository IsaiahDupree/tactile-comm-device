# Migration Guide: Legacy to Future-Proof System

## Overview
This guide helps you migrate from the existing folder-based system to the new future-proof playlist-based system.

## Key Changes

### 1. Directory Structure
**OLD:** `/01/`, `/02/`, etc. with mixed human/generated content
**NEW:** `/audio/human/{KEY}/` and `/audio/generated/{KEY}/` with strict separation

### 2. Hardware Mapping
**OLD:** Hardcoded GPIO -> label mappings in Arduino code
**NEW:** `/config/buttons.csv` defines all hardware mappings

### 3. Audio Selection
**OLD:** Folder scanning with hardcoded track ranges
**NEW:** Playlist-enforced ordering via `.m3u` files

## Migration Steps

### Step 1: Copy Audio Files
For each existing folder (01-35), copy files to the new structure:

```bash
# Example for folder 01 (A button)
# Human recordings (REC bank)
cp /01/001.mp3 /audio/human/A/001.mp3
cp /01/002.mp3 /audio/human/A/002.mp3
cp /01/003.mp3 /audio/human/A/003.mp3

# Generated audio (TTS bank)
cp /01/004.mp3 /audio/generated/A/001.mp3
cp /01/005.mp3 /audio/generated/A/002.mp3
cp /01/006.mp3 /audio/generated/A/003.mp3
```

### Step 2: Update Playlists
Edit the `.m3u` files in `/mappings/playlists/` to reflect your actual audio files.

### Step 3: Configure Hardware
Update `/config/buttons.csv` to match your physical button layout.

### Step 4: Test System
Use the new firmware's test commands:
- `T` - Test all buttons
- `U` - Verify audio files
- `P` - Print current mappings

## Mapping Reference

### A (Apple)
- **Legacy:** Folder 1 (REC: 1-3), Folder 1 (TTS: 4-6)
- **New:** `/audio/human/A/` and `/audio/generated/A/`

### B (Ball)
- **Legacy:** Folder 0 (REC: 0-none), Folder 2 (TTS: 1-7)
- **New:** `/audio/human/B/` and `/audio/generated/B/`

### C (Cat)
- **Legacy:** Folder 0 (REC: 0-none), Folder 3 (TTS: 1-7)
- **New:** `/audio/human/C/` and `/audio/generated/C/`

### D (Dog)
- **Legacy:** Folder 4 (REC: 1-1), Folder 4 (TTS: 2-6)
- **New:** `/audio/human/D/` and `/audio/generated/D/`

### E (Elephant)
- **Legacy:** Folder 0 (REC: 0-none), Folder 5 (TTS: 1-1)
- **New:** `/audio/human/E/` and `/audio/generated/E/`

### F (FaceTime)
- **Legacy:** Folder 0 (REC: 0-none), Folder 6 (TTS: 1-3)
- **New:** `/audio/human/F/` and `/audio/generated/F/`

### G (Good)
- **Legacy:** Folder 7 (REC: 1-1), Folder 7 (TTS: 2-3)
- **New:** `/audio/human/G/` and `/audio/generated/G/`

### H (Hello)
- **Legacy:** Folder 8 (REC: 1-2), Folder 8 (TTS: 3-7)
- **New:** `/audio/human/H/` and `/audio/generated/H/`

### I (Ice)
- **Legacy:** Folder 0 (REC: 0-none), Folder 9 (TTS: 1-3)
- **New:** `/audio/human/I/` and `/audio/generated/I/`

### J (Jump)
- **Legacy:** Folder 0 (REC: 0-none), Folder 10 (TTS: 1-1)
- **New:** `/audio/human/J/` and `/audio/generated/J/`

### K (Key)
- **Legacy:** Folder 11 (REC: 1-2), Folder 11 (TTS: 3-5)
- **New:** `/audio/human/K/` and `/audio/generated/K/`

### M (Mom)
- **Legacy:** Folder 0 (REC: 0-none), Folder 13 (TTS: 1-6)
- **New:** `/audio/human/M/` and `/audio/generated/M/`

### N (No)
- **Legacy:** Folder 14 (REC: 1-2), Folder 14 (TTS: 3-5)
- **New:** `/audio/human/N/` and `/audio/generated/N/`

### O (Orange)
- **Legacy:** Folder 0 (REC: 0-none), Folder 15 (TTS: 1-2)
- **New:** `/audio/human/O/` and `/audio/generated/O/`

### P (Please)
- **Legacy:** Folder 0 (REC: 0-none), Folder 16 (TTS: 1-4)
- **New:** `/audio/human/P/` and `/audio/generated/P/`

### Q (Queen)
- **Legacy:** Folder 0 (REC: 0-none), Folder 17 (TTS: 1-1)
- **New:** `/audio/human/Q/` and `/audio/generated/Q/`

### R (Red)
- **Legacy:** Folder 0 (REC: 0-none), Folder 18 (TTS: 1-3)
- **New:** `/audio/human/R/` and `/audio/generated/R/`

### S (Susu)
- **Legacy:** Folder 19 (REC: 1-1), Folder 19 (TTS: 2-10)
- **New:** `/audio/human/S/` and `/audio/generated/S/`

### T (Thank)
- **Legacy:** Folder 0 (REC: 0-none), Folder 20 (TTS: 1-4)
- **New:** `/audio/human/T/` and `/audio/generated/T/`

### U (Up)
- **Legacy:** Folder 21 (REC: 1-1), Folder 21 (TTS: 2-2)
- **New:** `/audio/human/U/` and `/audio/generated/U/`

### V (Very)
- **Legacy:** Folder 0 (REC: 0-none), Folder 22 (TTS: 1-1)
- **New:** `/audio/human/V/` and `/audio/generated/V/`

### W (Water)
- **Legacy:** Folder 23 (REC: 1-2), Folder 23 (TTS: 3-4)
- **New:** `/audio/human/W/` and `/audio/generated/W/`

### X (X-ray)
- **Legacy:** Folder 0 (REC: 0-none), Folder 24 (TTS: 1-1)
- **New:** `/audio/human/X/` and `/audio/generated/X/`

### Y (Yes)
- **Legacy:** Folder 0 (REC: 0-none), Folder 25 (TTS: 1-2)
- **New:** `/audio/human/Y/` and `/audio/generated/Y/`

### Z (Zebra)
- **Legacy:** Folder 0 (REC: 0-none), Folder 26 (TTS: 1-1)
- **New:** `/audio/human/Z/` and `/audio/generated/Z/`

### SPACE (Space)
- **Legacy:** Folder 0 (REC: 0-none), Folder 35 (TTS: 1-1)
- **New:** `/audio/human/SPACE/` and `/audio/generated/SPACE/`

### . (Period)
- **Legacy:** Folder 0 (REC: 0-none), Folder 33 (TTS: 1-3)
- **New:** `/audio/human/./` and `/audio/generated/./`


## Benefits of New System

1. **Hardware Independence:** Change GPIO pins without code changes
2. **Desktop App Ready:** Standard playlists work with any audio tool
3. **Strict Separation:** Human and generated audio never mixed
4. **Future Proof:** Easy to add new keys, hardware, or features
5. **Version Control:** Manifest tracks system changes
6. **Cross Platform:** Works on Windows, Mac, Linux

## Troubleshooting

- **No audio plays:** Check playlist files point to existing audio files
- **Wrong button mapping:** Update `/config/buttons.csv`
- **Priority not working:** Verify `/config/mode.cfg` settings
- **Missing playlists:** Use `U` command to verify all required files exist

For more help, see the main README.md file.
