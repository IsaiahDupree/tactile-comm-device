# Audio File Organization

This directory contains the audio files for the tactile communication device, organized by folder numbers that correspond to button mappings.

## Folder Structure

```
audio/
├── 01/          # Special buttons (YES, NO, WATER, HELP)
├── 05/          # Letter A variations
├── 06/          # Letter B variations
├── 07/          # Letter C variations
...
├── 30/          # Letter Z variations
├── 31/          # SPACE button
├── 32/          # PERIOD button
└── 33/          # SHIFT/HELP system
```

## File Naming Convention

Within each numbered folder:
- `001.mp3` - First press audio
- `002.mp3` - Second press audio  
- `003.mp3` - Third press audio
- etc.

## Audio Quality Guidelines

- **Format**: MP3
- **Sample Rate**: 22kHz or 44.1kHz
- **Bit Rate**: 128kbps minimum
- **Duration**: Keep under 5 seconds for responsiveness
- **Volume**: Normalize to consistent levels

## Content Types

### Generated TTS (Text-to-Speech)
- Clear, consistent pronunciation
- Good for common words and phrases
- Professional voice quality

### Recorded Personal Audio
- Family member voices
- Names and personal phrases
- Familiar, comforting sounds

## Button-to-Folder Mapping

| Button Label | Folder | Example Content |
|-------------|--------|----------------|
| YES | 01 | "Yes" |
| NO | 01 | "No" |  
| WATER | 01 | "Water" |
| HELP | 01 | "Help" |
| A | 05 | "Apple", "Amer", "Alari" |
| B | 06 | "Ball", "Bye", "Bathroom" |
| C | 07 | "Cat", "Chair", "Car" |
| ... | ... | ... |
| Z | 30 | "Zebra" |
| SPACE | 31 | "Space" |
| PERIOD | 32 | "Period" |
| SHIFT | 33 | "Shift", "Help" |

## Multi-Press System

When the same button is pressed multiple times within 1 second:
1. First press → plays 001.mp3
2. Second press → plays 002.mp3
3. Third press → plays 003.mp3
4. Continues cycling through available files
5. Wraps back to 001.mp3 after last file

## Adding New Audio

1. Record or generate new audio file
2. Save as MP3 format
3. Name sequentially (001.mp3, 002.mp3, etc.)
4. Place in appropriate numbered folder
5. Test with device

## Audio Preparation Tips

### For Recording Personal Audio
- Use quiet environment
- Speak clearly and at normal pace
- Keep consistent volume
- Save multiple takes if needed

### For TTS Generation
- Use high-quality TTS services
- Choose clear, easy-to-understand voices
- Test pronunciation of names and special words
- Maintain consistent speaking style

## SD Card Setup

1. Format SD card as FAT32
2. Copy numbered folders to SD card root
3. Ensure all audio files are properly named
4. Insert SD card into device
5. Power on and test audio playback
