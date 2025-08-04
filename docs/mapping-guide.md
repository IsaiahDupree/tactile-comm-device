# Button Mapping Guide

This guide explains how to configure button mappings and organize audio files for the tactile communication device.

## Audio File Organization

### Folder Structure

The device uses a numbered folder system on the SD card:

| Folder | Purpose | Examples |
|--------|---------|----------|
| `/01/` | Special buttons | YES, NO, WATER, HELP |
| `/05/` | Letter A | Apple, Amer, Alari, Arabic |
| `/06/` | Letter B | Ball, Bye, Bathroom, Bed |
| `/07/` | Letter C | Cat, Chair, Car |
| ... | ... | ... |
| `/30/` | Letter Z | Zebra |
| `/31/` | SPACE | Space |
| `/32/` | PERIOD | Period |
| `/33/` | SHIFT/HELP | Shift, Device Help |

### File Naming Convention

Within each folder, files are numbered sequentially:
- `001.mp3` - First press
- `002.mp3` - Second press  
- `003.mp3` - Third press
- etc.

## Multi-Press System

### How Multi-Press Works

When you press the same button multiple times within 1 second, the device cycles through different audio files:

**Example for "A" button:**
1. First press → `/05/001.mp3` (Apple - TTS)
2. Second press → `/05/002.mp3` (Amer - recorded)
3. Third press → `/05/003.mp3` (Alari - recorded)
4. Fourth press → `/05/004.mp3` (Arabic - TTS)
5. Fifth press → Wraps back to `/05/001.mp3`

### Audio Types

- **TTS (Text-to-Speech)**: Clear, consistent pronunciation
- **Recorded**: Personal, familiar voices from family/caregivers

## Configuration File Format

### config.csv Structure

The `config.csv` file on the SD card root maps physical buttons to labels:

```csv
index,label
0,A
1,B
2,C
3,D
4,E
...
30,SPACE
31,PERIOD
32,YES
33,NO
34,WATER
35,HELP
```

### Button Index Mapping

| Index Range | Hardware | Notes |
|-------------|----------|-------|
| 0-15 | PCF8575 #1 (0x20) | GPIO 0-15 |
| 16-31 | PCF8575 #2 (0x21) | GPIO 16-31 |
| 32-35 | Arduino pins | Pins 8, 9, 2, 5 |

## Detailed Audio Mappings

### Special Buttons (Folder 01)

| Button | Track | Content | Type |
|--------|-------|---------|------|
| YES | 001 | "Yes" | TTS |
| NO | 002 | "No" | TTS |
| WATER | 003 | "Water" | TTS |
| HELP | 004 | "Help" | TTS |

### Letter Buttons

Each letter has multiple variations. Here are some examples:

#### A Button (Folder 05)
1. `001.mp3` - "Apple" (TTS)
2. `002.mp3` - "Amer" (recorded name)
3. `003.mp3` - "Alari" (recorded name)
4. `004.mp3` - "Arabic" (TTS)
5. `005.mp3` - "Amory" (recorded name)

#### B Button (Folder 06)
1. `001.mp3` - "Ball" (TTS)
2. `002.mp3` - "Bye" (recorded)
3. `003.mp3` - "Bathroom" (TTS)
4. `004.mp3` - "Bed" (TTS)

#### K Button (Folder 15)
1. `001.mp3` - "Key" (TTS)
2. `002.mp3` - "Kiyah" (recorded name)
3. `003.mp3` - "Kyan" (recorded name)
4. `004.mp3` - "Kleenex" (TTS)

## Adding New Audio Content

### 1. Recording Personal Audio

For recorded content (family names, personal phrases):
- Record in clear, quiet environment
- Save as MP3 format
- Keep files under 5 seconds for best performance
- Use consistent volume levels

### 2. Generating TTS Audio

For consistent pronunciation:
- Use high-quality TTS services (11Labs, Azure, etc.)
- Choose clear, easy-to-understand voices
- Maintain consistent speaking pace
- Save as MP3, 22kHz recommended

### 3. File Placement

1. Determine the appropriate folder number
2. Number the file sequentially (001, 002, etc.)
3. Copy to SD card
4. Test with the device

## Calibration Process

### Interactive Calibration

1. Power on device with Serial Monitor open (115200 baud)
2. Press `C` to enter calibration mode
3. Press any physical button
4. Type the label (e.g., "A", "WATER", "HELP")
5. Press Enter to confirm
6. Repeat for all buttons
7. Press `E` to exit calibration
8. Press `S` to save configuration

### Manual Configuration

You can also edit `config.csv` directly:

1. Remove SD card from device
2. Edit `config.csv` on computer
3. Save changes
4. Reinsert SD card
5. Press `L` to load new configuration

## Advanced Mapping

### Custom Labels

You can create custom labels for specific needs:
- `PAIN` - for medical communication
- `TIRED` - for comfort needs
- `LOVE` - for emotional expression
- `PHONE` - for communication requests

### Priority System

The firmware includes a priority system:
1. **Human recorded** - Personal, familiar voices
2. **TTS generated** - Clear, consistent fallback

When audio files are missing, the device will:
1. Try the requested track
2. Fall back to track 001 in the same folder
3. Show helpful error messages in serial log

## Testing Your Configuration

### Button Test Command

Use `T` in Serial Monitor to test all configured buttons:
- Plays the first audio file for each mapped button
- Shows which files are missing
- Verifies button-to-audio mapping

### Individual Testing

Press any configured button to test:
- Single press plays first audio
- Multiple presses cycle through variations
- Serial log shows detailed information

### Troubleshooting Missing Audio

Common issues and solutions:

**File not found errors:**
- Check folder/file naming (must be exact)
- Verify SD card file system (FAT32)
- Ensure proper number formatting (001.mp3, not 1.mp3)

**No audio playback:**
- Check volume level (use `+` to increase)
- Verify speaker connections
- Test with known-good audio files

**Button not responding:**
- Verify button is mapped in config.csv
- Check hardware connections
- Use calibration mode to re-map
