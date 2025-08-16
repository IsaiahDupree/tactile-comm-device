# Tactile Communication Device - Future-Proof System

## Revolutionary Architecture

This is a complete rewrite of the tactile communication device firmware with a **hardware-agnostic, SD-card-defined architecture** that achieves true separation between hardware and software through strict configuration-driven design.

### Key Innovations

✅ **Complete Hardware Independence** - GPIO changes only require updating CSV files  
✅ **Strict Human/Generated Separation** - Never mix recording types  
✅ **Playlist-Enforced Ordering** - Desktop apps can precisely control playback order  
✅ **Third PCF8575 Support** - Up to 52 buttons total (3×16 + 4 GPIO)  
✅ **Desktop App Ready** - Standard file formats and versioned manifest  
✅ **Future-Proof Baseline** - Easy to extend without code changes  

## Hardware Support

### Supported Hardware
- **Arduino Uno/Nano** with VS1053 codec shield
- **Up to 3x PCF8575** I2C port expanders (addresses 0x20, 0x21, 0x22)
- **4x Direct GPIO pins** for special functions
- **Total capacity: 52 buttons** (48 from expanders + 4 direct)

### Hardware Mapping
Physical inputs are mapped via `/config/buttons.csv`:
```csv
#INPUT,KEY
pcf0:00,A        # PCF8575 #0, pin 0 → letter A
pcf1:15,Water    # PCF8575 #1, pin 15 → Water button
pcf2:10,Emergency # PCF8575 #2, pin 10 → Emergency button
gpio:8,Home      # Direct GPIO pin 8 → Home button
```

## SD Card Structure (Strict)

```
/config/
  mode.cfg                 # Global settings
  buttons.csv              # Hardware → key mapping

/mappings/
  playlists/
    A_human.m3u           # Human recordings for A
    A_generated.m3u       # Generated audio for A
    Water_human.m3u       # Human recordings for Water
    Water_generated.m3u   # Generated audio for Water
    ...

/audio/
  human/
    A/001.mp3, 002.mp3... # Human recordings by key
    Water/001.mp3...      # Human recordings for Water
    ...
  generated/
    A/001.mp3, 002.mp3... # Generated audio by key
    Water/001.mp3...      # Generated audio for Water
    SYSTEM/               # System announcements
      human_first.mp3
      generated_first.mp3
    ...

/state/
  cursors.json            # Optional: playback positions

/manifest.json            # Desktop app contract
```

## Priority System

### Two Modes
- **HUMAN_FIRST**: Play human recordings first, fallback to generated
- **GENERATED_FIRST**: Play generated audio first, fallback to human

### Control Methods
1. **Triple-press Period (.) button** - Toggle mode with voice announcement
2. **Serial command 'M'** - Toggle via console
3. **Edit `/config/mode.cfg`** - Direct file modification

### Mode Persistence
- Saved to EEPROM for power-cycle persistence
- Also saved to `/config/mode.cfg` for desktop app sync

## Playlist System

### Strict Ordering
All audio playback is controlled by `.m3u` playlist files:
```
# Human recordings for A
audio/human/A/001.mp3
audio/human/A/002.mp3
audio/human/A/003.mp3
```

### Desktop App Integration
- Standard M3U format works with any audio tool
- Cross-platform file paths (forward slashes)
- UTF-8 encoding for international characters
- One path per line, comments start with #

### Multi-Press Behavior
- Each press advances to the next track in the playlist
- Wraps to beginning when reaching the end
- Separate cursors for human vs generated playlists
- Priority mode determines which playlist is tried first

## Configuration Files

### `/config/mode.cfg`
```
PRIORITY=HUMAN_FIRST        # or GENERATED_FIRST
STRICT_PLAYLISTS=1          # 1=require playlists, 0=allow folder scan
```

### `/config/buttons.csv`
```csv
#INPUT,KEY
pcf0:00,A
pcf0:01,B
pcf2:15,Emergency
gpio:8,Home
```

### `/manifest.json` (Optional)
Versioned contract for desktop applications:
```json
{
  "schema": "tcd-playlists@1",
  "version": "1.0.0",
  "priority": "HUMAN_FIRST",
  "strict_playlists": true,
  "keys": [
    {
      "key": "A",
      "human_playlist": "mappings/playlists/A_human.m3u",
      "generated_playlist": "mappings/playlists/A_generated.m3u"
    }
  ]
}
```

## Serial Commands

| Command | Function |
|---------|----------|
| `L/l` | Load config from SD card |
| `S/s` | Save config to SD card |
| `P/p` | Print current mappings |
| `H/h` | Show help menu |
| `M/m` | Toggle priority mode |
| `T/t` | Test all buttons |
| `U/u` | Verify audio files and playlists |
| `C/c` | Enter calibration mode |
| `E/e` | Exit calibration mode |
| `X/x` | Stop current audio |
| `+` | Volume maximum |
| `-` | Volume moderate |
| `1-9` | Volume levels (1=max, 9=quiet) |

## Desktop App Development

### File Format Standards
- **Playlists**: Standard M3U format with UTF-8 encoding
- **Paths**: Forward slashes, relative to SD root
- **Audio**: MP3 format, any bitrate/sample rate
- **Config**: Simple INI-style or CSV format

### Versioning Contract
The `manifest.json` provides a stable API:
- Schema version for compatibility checking
- Complete key inventory with file paths
- Hardware configuration summary
- Current settings snapshot

### Cross-Platform Compatibility
- Windows, Mac, Linux compatible file paths
- FAT32 filesystem constraints respected
- No special characters in filenames
- Standard audio formats only

## Migration from Legacy System

### Automatic Migration
Use the included `generate_future_proof_playlists.py` script:
1. Analyzes your existing folder structure
2. Creates new directory layout
3. Generates playlist files
4. Provides migration instructions

### Manual Migration Steps
1. **Copy audio files** from numbered folders to key-based folders
2. **Update playlists** to reflect actual audio content
3. **Configure hardware** via `buttons.csv`
4. **Test system** with new firmware

See `MIGRATION_GUIDE.md` for detailed instructions.

## Benefits Over Legacy System

### Hardware Independence
- **Before**: GPIO changes required code recompilation
- **After**: GPIO changes only need CSV file updates

### Content Management
- **Before**: Hardcoded track ranges, mixed human/generated content
- **After**: Playlist-controlled ordering, strict separation

### Desktop Integration
- **Before**: No desktop tool support
- **After**: Standard formats work with any audio application

### Extensibility
- **Before**: Adding keys required code changes
- **After**: Add keys by creating playlist files

### Maintenance
- **Before**: Technical knowledge required for any changes
- **After**: Non-technical users can manage content via files

## Troubleshooting

### No Audio Plays
- Check playlist files exist and point to valid audio files
- Use `U` command to verify all mapped files exist
- Ensure audio files are in MP3 format

### Wrong Button Mapping
- Update `/config/buttons.csv` with correct hardware mappings
- Use `L` command to reload configuration
- Use `P` command to verify current mappings

### Priority Mode Issues
- Check `/config/mode.cfg` has correct PRIORITY setting
- Triple-press Period button to toggle mode
- Use `M` command to toggle via serial console

### Missing Playlists
- Ensure both `{KEY}_human.m3u` and `{KEY}_generated.m3u` exist
- Use `U` command to verify all required playlists are present
- Check playlist files have correct audio file paths

## Future Enhancements

This architecture enables easy future enhancements:
- **More PCF8575 expanders** - Just update NUM_PCF constant
- **Network connectivity** - Add WiFi module for remote control
- **Voice recognition** - Add speech-to-text for dynamic responses
- **Cloud sync** - Sync playlists and settings across devices
- **Mobile app** - Standard file formats work with mobile tools
- **Multi-language** - Separate playlist sets per language

## Technical Details

### Memory Usage
- Dynamic allocation for button mappings
- Playlist caching for performance
- Minimal EEPROM usage (1 byte for priority mode)

### Performance
- 50ms scan rate for responsive button detection
- Edge detection prevents duplicate presses
- Interrupt-driven audio playback

### Reliability
- Graceful fallback if SD files missing
- Configuration validation on startup
- Error reporting via serial console

---

**This system represents the ultimate evolution of the tactile communication device - completely hardware-agnostic, desktop-app-ready, and future-proof for any enhancement you can imagine.**
