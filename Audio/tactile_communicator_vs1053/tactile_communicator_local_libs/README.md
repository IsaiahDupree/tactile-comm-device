# Tactile Communicator - Local Libraries Version

This is a self-contained Arduino project with all required libraries included locally.

## Project Structure

```
tactile_communicator_local_libs/
├── tactile_communicator_local_libs.ino    # Main Arduino sketch
├── Adafruit_VS1053.h                     # VS1053 audio codec library header
├── Adafruit_VS1053.cpp                   # VS1053 audio codec library source
├── PCF8575.h                             # PCF8575 I2C expander library header
├── PCF8575.cpp                           # PCF8575 I2C expander library source
├── config/                               # SD card configuration files
│   ├── buttons.csv                       # Hardware button mapping
│   ├── playlist.csv                      # Audio playlist mapping
│   └── audio_index.csv                   # Optional audio descriptions
├── LIBRARY_INFO.md                       # Library compatibility information
└── README.md                            # This file
```

## Required Hardware

- Arduino (Uno, Nano, etc.)
- VS1053 Audio Codec Breakout
- PCF8575 I2C GPIO Expanders (up to 2 units)
- SD Card for audio storage
- Tactile buttons
- Audio output (speakers/headphones)

## Pin Configuration

### VS1053 Audio Codec
- BREAKOUT_RESET: Pin 9
- BREAKOUT_CS: Pin 10
- BREAKOUT_DCS: Pin 8
- CARDCS: Pin 4
- DREQ: Pin 3

### Extra GPIO Pins
- A0, A1, A2, A3 (4 additional buttons)

### I2C (PCF8575 Expanders)
- PCF8575 #1: Address 0x20 (up to 16 buttons)
- PCF8575 #2: Address 0x21 (up to 16 buttons)
- SDA: A4 (Uno) / Pin 20 (Mega)
- SCL: A5 (Uno) / Pin 21 (Mega)

## SD Card Structure

The system expects the following structure on the SD card:

```
SD Card Root/
├── config/
│   ├── buttons.csv      # Hardware mapping (required)
│   ├── playlist.csv     # Audio playlists (required)
│   └── audio_index.csv  # Text descriptions (optional)
├── 01/ ... 33/          # TTS audio folders
├── 101/ ... 133/        # REC audio folders (+100 convention)
└── [audio files]        # MP3 files organized by folder
```

## Configuration Files

### buttons.csv
Maps physical button indices to logical labels:
```csv
2,K
3,A
5,P
# ... more mappings
```

### playlist.csv
Defines what audio plays for each button press:
```csv
A,1,TTS,/01/001.mp3,Letter A
A,2,TTS,/01/002.mp3,Apple
# label,press_count,bank,path,description
```

### audio_index.csv (Optional)
Provides human-readable descriptions for logging:
```csv
/01/001.mp3,Letter A
/02/001.mp3,Letter B
# path,description
```

## Features

- **Hardware Independence**: Change GPIO pins by editing `buttons.csv`
- **Multi-press Support**: Each button supports multiple press sequences
- **Priority Modes**: HUMAN_FIRST vs GENERATED_FIRST audio priority
- **Calibration Mode**: Interactive button mapping setup
- **Serial Commands**: Real-time configuration and testing

## Serial Commands

- `C/c` - Enter calibration mode
- `E/e` - Exit calibration mode
- `L/l` - Load config from SD
- `S/s` - Save button mappings
- `P/p` - Print current mappings
- `H/h` - Show help menu
- `M/m` - Toggle priority mode
- `T/t` - Test all buttons
- `U/u` - Check audio file sanity
- `X/x` - Stop current audio
- `+/-` - Volume control

## Special Functions

- **Period Button Triple-Press**: Toggle between HUMAN_FIRST and GENERATED_FIRST modes
- **Multi-Press Detection**: Buttons support 1, 2, 3+ presses with different audio
- **Audio Priority**: System respects human vs generated audio preferences

## Installation

1. Open `tactile_communicator_local_libs.ino` in Arduino IDE
2. Arduino IDE will automatically detect local libraries
3. Compile and upload to your Arduino
4. Prepare SD card with proper structure and audio files
5. Configure `buttons.csv` and `playlist.csv` for your setup

## Troubleshooting

- **Compilation Errors**: Ensure all libraries are in the `libraries/` folder
- **SD Card Issues**: Verify SD card formatting (FAT32) and file structure
- **Audio Problems**: Check VS1053 wiring and audio file formats (MP3)
- **Button Issues**: Use calibration mode to map buttons correctly
- **I2C Problems**: Verify PCF8575 addresses and wiring

## Library Sources

- **Adafruit_VS1053_Library**: Official Adafruit library for VS1053 codec
- **PCF8575**: RobTillaart's PCF8575 library from GitHub

This project is completely self-contained and doesn't require external library installation.
