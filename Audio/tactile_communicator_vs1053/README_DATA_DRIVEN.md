# Tactile Communication Device - Data-Driven Architecture

## Overview

This is a completely rewritten, future-proof version of the tactile communication device that separates hardware concerns from content concerns. The system is now **100% data-driven** and **label-centric**.

## Key Benefits

✅ **Hardware Independence**: GPIO pin changes only require updating CSV files - no code changes  
✅ **Content Flexibility**: Add/remove/reorder audio clips without recompilation  
✅ **Multi-Press Support**: Each button can have unlimited audio clips accessed via multiple presses  
✅ **Priority Mode**: Supports REC vs TTS priority selection  
✅ **Full Path Control**: Reference any audio file anywhere on SD card  
✅ **Easy Maintenance**: Human-readable CSV configuration files  

## File Structure

```
Arduino Project/
├── tactile_communicator_vs1053_data_driven.ino  <- New data-driven firmware
├── tactile_communicator_vs1053_backup.ino       <- Backup of original
└── config/                                       <- Sample SD card config
    ├── buttons.csv      <- Hardware GPIO → Label mapping
    ├── playlist.csv     <- Label → Audio clips (multi-press)
    └── audio_index.csv  <- Optional text manifest for logging

SD Card Layout:
/01 ... /33     <- TTS folders (text-to-speech)
/101 ... /133   <- REC folders (personal recordings, +100 convention)
/config/        <- Configuration files (copy from Arduino project)
```

## Configuration Files

### 1. `/config/buttons.csv` - Hardware Mapping

Maps physical GPIO indices to button labels:

```csv
index,label
2,K
3,A
5,P
15,.
32,B
```

- **index**: GPIO pin number (0-31 for PCF8575, 32+ for direct pins)
- **label**: 1-3 character button label (K, A, P, ., SPACE, etc.)

### 2. `/config/playlist.csv` - Content Mapping

Maps button labels to ordered audio clips for multi-press:

```csv
label,press,bank,path,text
S,1,REC,/123/001.mp3,Susu
S,2,TTS,/23/002.mp3,Sad
S,3,TTS,/23/003.mp3,Scarf
K,1,REC,/115/001.mp3,Kaiser
K,2,REC,/115/002.mp3,Kiyah
```

- **label**: Button label (must match buttons.csv)
- **press**: Press sequence number (1, 2, 3, ...)
- **bank**: Audio type ("REC" or "TTS") for priority mode
- **path**: Full path to MP3 file on SD card
- **text**: Human-readable description for console logging

### 3. `/config/audio_index.csv` - Text Manifest (Optional)

Provides text descriptions for console logging:

```csv
folder,track,text,bank
23,2,Sad,TTS
115,1,Kaiser,REC
```

## How It Works

### 1. Hardware Independence
```
Button Press → GPIO Index → Label (via buttons.csv) → Audio Clips (via playlist.csv)
```

### 2. Multi-Press Behavior
- Press button once: plays clip with `press=1`
- Press button twice quickly: plays clip with `press=2`
- Press button N times: plays clip with `press=N` (wraps around if more presses than clips)

### 3. Priority Mode
- **HUMAN_FIRST**: Prefers REC bank clips over TTS
- **GENERATED_FIRST**: Prefers TTS bank clips over REC
- Toggle by triple-pressing the Period (.) button

## Usage Instructions

### Initial Setup
1. Copy the `config/` folder to your SD card root
2. Ensure audio files exist at the paths specified in `playlist.csv`
3. Upload `tactile_communicator_vs1053_data_driven.ino` to Arduino
4. Open Serial Monitor to see status messages

### Adding New Buttons
1. Enter calibration mode: Send `C` via Serial Monitor
2. Press the physical button you want to configure
3. Type the desired label (e.g., "X") and press Enter
4. Exit calibration: Send `E` via Serial Monitor
5. Save mappings: Send `S` via Serial Monitor

### Adding Audio Content
1. Edit `playlist.csv` to add new clips for any label
2. Use full paths (e.g., `/25/003.mp3`) to reference audio files
3. Reload config: Send `L` via Serial Monitor

### Changing Hardware Wiring
1. Update `buttons.csv` with new GPIO index → label mappings
2. Reload config: Send `L` via Serial Monitor
3. **No code changes needed!**

## Serial Commands

- `C` - Enter calibration mode
- `E` - Exit calibration mode  
- `L` - Load/reload configuration from SD card
- `S` - Save button mappings to SD card
- `P` - Print current button mappings
- `T` - Test all configured buttons
- `U` - Check audio file sanity (verify files exist)
- `M` - Toggle priority mode
- `X` - Stop current audio playback
- `+/-` - Volume control

## Migration from Original System

The original system used hardcoded arrays and folder+base+count logic. This new system:

1. **Replaces hardcoded mappings** with dynamic CSV loading
2. **Replaces folder math** with explicit full paths  
3. **Adds multi-press support** with ordered playlists
4. **Maintains all existing features** (priority mode, calibration, etc.)

## Troubleshooting

### "No clips found for label"
- Check that `playlist.csv` contains entries for that label
- Verify label spelling matches between `buttons.csv` and `playlist.csv`

### "File not found"
- Verify audio files exist at the exact paths in `playlist.csv`
- Check SD card file system and folder structure

### Button not responding
- Check `buttons.csv` for correct GPIO index mapping
- Use calibration mode to verify button detection
- Send `P` to print current mappings

## Technical Notes

- **Memory**: Uses dynamic allocation for configuration arrays
- **Performance**: CSV parsing happens only at startup/reload
- **Compatibility**: Works with existing VS1053 and PCF8575 hardware
- **Limits**: 16 clips per button label (configurable in code)

This architecture makes the system completely future-proof - all changes can be made via CSV files without touching Arduino code!
