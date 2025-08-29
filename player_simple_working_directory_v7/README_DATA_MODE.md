# Data Mode Testing & Development

This v6 firmware includes a complete data mode implementation for SD card debugging and development.

## Features Added

### Data Mode Protocol
- **PUT/GET/DEL/LS/EXIT** commands via serial
- **CRC32 verification** for file integrity
- **Atomic file operations** with .part temporary files
- **Write protection** via `/config/allow_writes.flag`
- **Auto-timeout** after 30s of inactivity

### Entry Methods
1. **Serial handshake**: Send `^DATA? v1` + Enter
2. **PERIOD×4 + confirm**: Press PERIOD 4 times, then send `!` within 3s

## Quick Start

### 1. Enable Writes
Create an empty file at `/config/allow_writes.flag` on the SD card.

### 2. Install Python CLI
```bash
pip install pyserial
```

### 3. Test Commands

**List available ports:**
```bash
python data_cli.py ports
```

**Enter data mode and list files:**
```bash
python data_cli.py ls -p COM6 human A
```

**Upload a file:**
```bash
python data_cli.py put -p COM6 human A 001.mp3 ./local/001.mp3
```

**Download a file:**
```bash
python data_cli.py get -p COM6 human A 001.mp3 ./out/001.mp3
```

**Delete a file:**
```bash
python data_cli.py del -p COM6 human A 001.mp3
```

**Exit data mode:**
```bash
python data_cli.py exit -p COM6
```

## Directory Structure
- `/audio/human/[KEY]/` - Human recordings
- `/audio/generated/[KEY]/` or `/audio/GENERA~1/[KEY]/` - Generated audio
- `/config/allow_writes.flag` - Write permission flag

## Development Notes
- Uses 115200 baud (can be increased to 500k/1M later)
- 512-byte I/O buffers for efficiency
- Supports both `generated` and `GENERA~1` paths for FAT32 compatibility
- CRC32 verification optional but recommended
- Progress indicators for large file transfers

## Debugging
- Serial monitor shows `[DATA] mode=ENTER` when entering data mode
- Device responds `DATA:OK v1` to handshake
- `DATA:IDLE` indicates timeout exit
- `ERR:WRITELOCK` means missing allow_writes.flag

## Integration with Existing Firmware
- Data mode completely bypasses normal button/audio processing
- Audio playback stops when entering data mode
- Normal operation resumes after exit
- All existing v5 features preserved (SHIFT mapping, YES/NO variants, etc.)
