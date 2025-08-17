# Tactile Communication Device - Button Mappings Reference

**Document Version:** 1.0  
**Date:** August 13, 2025  
**Device:** Tactile Communication Device for PSP/Low-Vision Users

---

## Overview

This document provides a complete reference for all button mappings on the tactile communication device. Each button can be pressed multiple times to cycle through different phrases and words.

### How Multi-Press Works
- **Single Press:** Plays the first audio file
- **Multiple Presses:** Cycles through additional variations within 1 second
- **Audio Types:** Mix of TTS (Text-to-Speech) and recorded personal voices

---

## Special Function Buttons

| Button | Folder | Audio Files |
|--------|--------|-------------|
| **YES** | `/01/` | Yes |
| **NO** | `/01/` | No |
| **WATER** | `/01/` | Water |
| **AUX/HELP** | `/01/` | Hello How are You |

---

## Letter Button Mappings

### A Button (Folder `/05/`)
1. **Amer** (recorded name)
2. **Alari** (recorded name)  
3. **Apple** (TTS)
4. **Arabic Show** (TTS)

### B Button (Folder `/06/`)
1. **Bathroom** (TTS)
2. **Bye** (recorded)
3. **Bed** (TTS)
4. **Breathe** (TTS)
5. **Blanket** (TTS)

### C Button (Folder `/07/`)
1. **Chair** (TTS)
2. **Car** (TTS)
3. **Cucumber** (TTS)

### D Button (Folder `/08/`)
1. **Deen** (recorded name)
2. **Daddy** (recorded)
3. **Doctor** (TTS)
4. **Door** (TTS)

### E Button (Folder `/09/`)
*Currently no audio files assigned*

### F Button (Folder `/10/`)
1. **FaceTime** (TTS)
2. **Funny** (TTS)

### G Button (Folder `/11/`)
1. **Good Morning** (TTS)
2. **Go** (TTS)

### H Button (Folder `/12/`)
1. **How are you** (TTS)
2. **Heartburn** (TTS)

### I Button (Folder `/13/`)
1. **Inside** (TTS)

### J Button (Folder `/14/`)
*Currently no audio files assigned*

### K Button (Folder `/15/`)
1. **Kiyah** (recorded name)
2. **Kyan** (recorded name)
3. **Kleenex** (TTS)
4. **Kaiser** (TTS)

### L Button (Folder `/16/`)
1. **Lee** (recorded name)
2. **I love you** (recorded/TTS)
3. **Light down** (TTS)
4. **Light up** (TTS)

### M Button (Folder `/17/`)
1. **Mohammad** (recorded name)
2. **Medicine** (TTS)
3. **Medical** (TTS)

### N Button (Folder `/18/`)
1. **Nada** (recorded name)
2. **Nadowie** (recorded name)
3. **Noah** (recorded name)

### O Button (Folder `/19/`)
1. **Outside** (TTS)

### P Button (Folder `/20/`)
1. **Pain** (TTS)
2. **Phone** (TTS)

### Q Button (Folder `/21/`)
*Currently no audio files assigned*

### R Button (Folder `/22/`)
1. **Room** (TTS)

### S Button (Folder `/23/`)
1. **Scarf** (TTS)
2. **Susu** (recorded name)
3. **Sinemet** (TTS - medication name)

### T Button (Folder `/24/`)
1. **TV** (TTS)

### U Button (Folder `/25/`)
1. **Urgent Care** (TTS)

### V Button (Folder `/26/`)
*Currently no audio files assigned*

### W Button (Folder `/27/`)
1. **Water** (TTS)
2. **Walker** (TTS)
3. **Wheelchair** (TTS)
4. **Walk** (TTS)

### X Button (Folder `/28/`)
*Currently no audio files assigned*

### Y Button (Folder `/29/`)
*Currently no audio files assigned*

### Z Button (Folder `/30/`)
*Currently no audio files assigned*

---

## Punctuation and Special Characters

| Button | Folder | Function |
|--------|--------|----------|
| **SPACE** | `/31/` | Space character |
| **PERIOD** | `/32/` | Period (.) |

---

## Hardware Button Layout

### PCF8575 Port Expander #1 (Address 0x20)
- **Buttons 0-15:** Letters A-P
- **I²C Connection:** SDA/SCL pins

### PCF8575 Port Expander #2 (Address 0x21)  
- **Buttons 16-31:** Letters Q-Z, SPACE, PERIOD
- **I²C Connection:** SDA/SCL pins

### Direct Arduino Pins
- **Pin 8:** YES button
- **Pin 9:** NO button  
- **Pin 2:** WATER button
- **Pin 5:** AUX/HELP button

---

## Audio File Organization

### File Structure on SD Card
```
/01/    Special buttons (YES, NO, WATER, HELP)
/05/    Letter A variations
/06/    Letter B variations
...
/30/    Letter Z variations
/31/    SPACE
/32/    PERIOD
```

### File Naming Convention
- `001.mp3` - First press audio
- `002.mp3` - Second press audio
- `003.mp3` - Third press audio
- etc.

---

## Device Controls

### Serial Monitor Commands (115200 baud)
- **`C`** - Enter calibration mode
- **`P`** - Print current button mappings
- **`T`** - Test all configured buttons
- **`+/-`** - Adjust volume up/down
- **`1-9`** - Set specific volume levels
- **`X`** - Stop current audio playback
- **`L`** - Load configuration from SD card
- **`S`** - Save current configuration

---

## Notes for Caregivers

### Personal Names and Recordings
The device includes many personal recorded names:
- **Family:** Amer, Alari, Deen, Kiyah, Kyan, Lee, Mohammad, Nada, Nadowie, Noah, Susu
- **Recorded by:** Family members for familiar voice recognition

### Medical/Care Terms
- **Sinemet:** Parkinson's medication
- **Kaiser:** Healthcare provider
- **Urgent Care:** Medical facility
- **Pain, Medicine, Medical:** Health-related communications

### Daily Living
- **Bathroom, Bed, Chair, Water, Walker, Wheelchair:** Essential daily needs
- **TV, Phone, FaceTime:** Communication and entertainment
- **Light up/down:** Environmental controls

---

## Troubleshooting

### If Button Doesn't Respond
1. Check if button is mapped in configuration
2. Verify hardware connections
3. Use calibration mode (`C`) to re-map
4. Check Serial Monitor for error messages

### If No Audio Plays
1. Check volume level (press `+` to increase)
2. Verify speaker connections
3. Ensure SD card is properly inserted
4. Check that audio files exist in correct folders

### Missing Audio Files
- Device will attempt to play requested file
- Falls back to `001.mp3` in same folder if file missing
- Check Serial Monitor for "file not found" messages

---

**Document prepared for:** Tactile Communication Device Project  
**Target User:** Individual with Progressive Supranuclear Palsy (PSP)  
**Project Type:** Open-source assistive technology  
**License:** MIT License
