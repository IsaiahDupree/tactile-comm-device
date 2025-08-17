# VS1053 Audio Player - Simple Example

A complete, self-contained Arduino project for the Adafruit VS1053 Audio Codec Shield with local library dependencies.

## Overview

This project demonstrates basic audio playback functionality using the VS1053 codec with an Arduino. It includes all necessary libraries locally to ensure compatibility and easy deployment.

## Hardware Requirements

- Arduino Uno/Nano/Mega
- Adafruit VS1053 Codec Breakout or Shield
- MicroSD card with audio files
- Proper SPI connections

## Pin Configuration

```cpp
#define SHIELD_RESET  -1   // reset is tied high on the shield
#define SHIELD_CS      7   // VS1053 xCS
#define SHIELD_DCS     6   // VS1053 xDCS
#define CARDCS         4   // micro-SD CS
#define DREQ           3   // VS1053 DREQ (INT1 on Uno)
```

## Features

- **Complete Audio Playback**: Plays MP3 files from SD card
- **Background Playback**: Uses interrupt-driven playback
- **Serial Control**:
  - Send 's' to stop playback
  - Send 'p' to pause/unpause
- **File Listing**: Displays all files on SD card at startup
- **Local Libraries**: All dependencies included locally
- **Arduino R4 Compatible**: Tested with Arduino Uno R4 WiFi

## SD Card Setup

Place MP3 files on the root of your SD card:
- `track001.mp3` - First track (plays to completion)
- `track002.mp3` - Second track (plays in background)

## Local Libraries Included

- **Adafruit_VS1053**: Modified for Arduino R4 compatibility
- **Adafruit_BusIO**: SPI/I2C abstraction layer
- **SD Library**: Standard Arduino SD card support

## Usage

1. Load the sketch in Arduino IDE
2. Connect VS1053 shield/breakout according to pin configuration
3. Insert SD card with MP3 files
4. Upload and run
5. Open Serial Monitor to see status and control playback

## Compatibility Notes

This version includes fixes for Arduino Uno R4 WiFi compatibility:
- Proper SD card deselection during VS1053 initialization
- Updated library includes for Renesas architecture
- Interrupt handling improvements

## License

BSD license - see individual library files for specific licensing terms.

## Credits

Based on Adafruit VS1053 library examples with modifications for improved compatibility and local library integration.
