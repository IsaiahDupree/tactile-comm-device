# Tactile Communication Device - Data-Driven Version

A complete, self-contained Arduino project for an advanced tactile communication device with VS1053 audio codec, PCF8575 I2C expanders, and data-driven configuration system.

## Overview

This project implements a sophisticated tactile communication device with:
- Hardware-independent button mapping via CSV configuration
- Multi-press support with playlist-driven audio
- Priority modes (Human-first vs Generated-first audio)
- Complete calibration system via serial interface
- Local libraries for maximum compatibility

## Hardware Requirements

- Arduino Uno/Nano/Mega (tested with Arduino Uno R4 WiFi)
- Adafruit VS1053 Codec Breakout
- 2x PCF8575 I2C GPIO Expanders (addresses 0x20, 0x21)
- MicroSD card with structured audio files
- Up to 32 tactile buttons (via PCF8575) + 4 direct GPIO pins

## Pin Configuration

### VS1053 Audio Codec
```cpp
#define BREAKOUT_RESET  9   // VS1053 reset
#define BREAKOUT_CS     10  // VS1053 xCS
#define BREAKOUT_DCS    8   // VS1053 xDCS
#define CARDCS          4   // SD card CS
#define DREQ            3   // VS1053 DREQ
```

### I2C Expanders
- PCF8575 #1: Address 0x20 (buttons 0-15)
- PCF8575 #2: Address 0x21 (buttons 16-31)

### Direct GPIO Pins
- A0, A1, A2, A3 (buttons 32-35)

## Features

### 🎛️ **Advanced Configuration System**
- **Serial Commands**: Full menu-driven interface
  - `C/c`: Enter calibration mode
  - `E/e`: Exit calibration mode
  - `S/s`: Save button mappings to SD
  - `L/l`: Load configuration from SD
  - `P/p`: Print current mappings
  - `H/h`: Show help menu
  - `M/m`: Toggle priority mode
  - `T/t`: Test all buttons
  - `U/u`: Audio sanity check
  - `X/x`: Stop current audio
  - `+/-`: Volume control

### 🔧 **Data-Driven Architecture**
- **Hardware Independence**: Button mappings via `/config/buttons.csv`
- **Flexible Playlists**: Multi-press sequences via `/config/playlist.csv`
- **Priority Modes**: Human-first vs Generated-first audio selection
- **Multi-Press Support**: Different audio for single/double/triple presses

### 🎵 **Audio Management**
- **Background Playback**: Interrupt-driven MP3 playback
- **Dual Audio Types**: TTS (generated) and REC (human recordings)
- **Smart Fallback**: Automatic fallback between audio types
- **Volume Control**: Serial-controlled volume adjustment

## SD Card Structure

```
/01/ ... /33/     ← TTS (Text-to-Speech) folders
/101/ ... /133/   ← REC (Human Recording) folders (+100 convention)
/config/
  ├── buttons.csv     ← GPIO index → label mapping
  ├── playlist.csv    ← label → ordered clips (multi-press)
  └── audio_index.csv ← optional text manifest for logging
```

### Sample Configuration Files

#### `/config/buttons.csv`
```csv
index,label
2,K
3,A
15,.
16,N
```

#### `/config/playlist.csv`
```csv
label,press,bank,path,text
A,1,TTS,/01/001.mp3,Letter A
A,2,REC,/101/001.mp3,Letter A Recording
.,1,TTS,/33/004.mp3,Human First Mode
.,2,TTS,/33/005.mp3,Generated First Mode
```

## Local Libraries Included

- **Adafruit_VS1053**: Modified for Arduino R4 compatibility
- **Adafruit_BusIO**: Complete SPI/I2C abstraction layer
- **PCF8575**: RobTillaart I2C GPIO expander library
- **Standard Libraries**: SPI, SD, Wire, EEPROM

## Usage

### Initial Setup
1. Load `tactile_communicator_data_driven_local.ino` in Arduino IDE
2. Connect hardware according to pin configuration
3. Prepare SD card with audio files and configuration
4. Upload and run
5. Open Serial Monitor (115200 baud)

### Calibration Process
1. Send `C` to enter calibration mode
2. Press any button to assign/update its label
3. Type the desired label (e.g., "A", "HELP", ".") and press Enter
4. Send `E` to exit calibration mode
5. Send `S` to save mappings to SD card

### Operation Modes
- **Human-First**: Prioritizes human recordings over TTS
- **Generated-First**: Prioritizes TTS over human recordings
- **Toggle**: Triple-press the period (.) button to switch modes

## Advanced Features

### Multi-Press Detection
- Single press: Play first audio in sequence
- Double press: Play second audio in sequence
- Triple press: Play third audio in sequence (if available)
- Period button: Triple-press toggles priority mode with voice announcement

### Priority System
- **HUMAN_FIRST**: Plays human recordings when available, falls back to TTS
- **GENERATED_FIRST**: Plays TTS when available, falls back to human recordings
- Settings persist across power cycles via EEPROM

### Hardware Independence
- GPIO pin assignments can change without code modification
- Only requires updating `/config/buttons.csv`
- Labels remain consistent across hardware changes
- Supports mixed PCF8575 and direct GPIO configurations

## Compatibility Notes

This version includes comprehensive compatibility fixes:
- **Arduino R4 WiFi**: Full support with Renesas architecture fixes
- **Local Libraries**: All dependencies included to avoid version conflicts
- **Platform Independence**: Works across Arduino Uno/Nano/Mega variants
- **I2C Stability**: Robust PCF8575 communication with error handling

## Troubleshooting

### Common Issues
1. **VS1053 not found**: Check SPI connections and power
2. **SD card failed**: Verify SD card format (FAT32) and connections
3. **No audio**: Check audio files exist and are valid MP3 format
4. **Buttons not responding**: Verify I2C addresses and PCF8575 connections
5. **Configuration not loading**: Ensure CSV files have correct format and headers

### Serial Commands for Debugging
- `H`: Show complete help menu
- `P`: Print all current button mappings
- `U`: Check for missing audio files
- `T`: Test all configured buttons

## License

BSD license - see individual library files for specific licensing terms.

## Credits

Based on advanced tactile communication device firmware with:
- Adafruit VS1053 library (modified for compatibility)
- RobTillaart PCF8575 library
- Data-driven architecture for maximum flexibility
