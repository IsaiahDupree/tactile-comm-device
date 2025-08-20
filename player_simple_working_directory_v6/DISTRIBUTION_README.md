# Tactile Data Tool

A GUI application for managing audio files on the Tactile Communication Device via USB serial connection.

## Quick Start

1. **Enable writes on device**: Put a blank file at `/config/allow_writes.flag` on the SD card (enables PUT/DELETE operations).
2. **Connect device**: Plug the device via USB.
3. **Launch app**: Run the executable → select the COM/tty port → Click **Connect**.
4. **Choose location**: Select bank (`human`/`generated`/`GENERA~1`) + key (e.g., `A`, `SHIFT`).
5. **Manage files**: Use **List**, **Upload**, **Download**, **Delete**, or **Sync**.
6. **Exit**: Click **Exit Data Mode** when done.

## Features

- **File Management**: Upload, download, delete audio files
- **Smart Sync**: Upload only changed/missing files (by size comparison)
- **Two Sync Modes**:
  - Sequential: Upload as `001.mp3`, `002.mp3`...
  - Preserve: Keep original filenames
- **Progress Tracking**: Real-time operation status and logs
- **CRC Verification**: Ensures file integrity during transfers

## Troubleshooting

**Connection Issues:**
- If Connect fails, try a different port or unplug/replug the device
- Windows may need a USB serial driver (check Device Manager)
- Try different baud rates if 115200 doesn't work

**Write Protection:**
- If you see `ERR:WRITELOCK`, add `/config/allow_writes.flag` to the SD card
- This is a safety feature to prevent accidental file modifications

**Device Not Responding:**
- Press PERIOD button 4 times + confirm to enter data mode manually
- Or send `^DATA? v1` via serial terminal to trigger data mode

## File Structure

The device organizes audio files as:
```
/audio/
  ├── human/          # Human-recorded audio
  │   ├── A/           # Button A sounds
  │   ├── B/           # Button B sounds
  │   └── ...
  ├── generated/      # TTS-generated audio  
  │   ├── SHIFT/       # SHIFT button sequences
  │   └── ...
  └── GENERA~1/       # FAT32 short name for "generated"
```

## Banks and Keys

- **Bank**: `human`, `generated`, or `GENERA~1` (for FAT32 compatibility)
- **Key**: Button identifier like `A`, `B`, `SHIFT`, `PERIOD`

## Technical Notes

- Uses 115200 baud serial communication
- Supports CRC32 verification for file integrity
- Atomic file operations (writes to `.part` files first)
- Auto-exits data mode after idle timeout
- Compatible with Arduino UNO R4 WiFi + VS1053 audio codec

## Support

For issues or questions, check the project repository or device documentation.
