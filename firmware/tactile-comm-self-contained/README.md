# Tactile Communication Device - Complete Local Libraries Version


## Overview

This is a complete, self-contained tactile communication device project with VS1053 audio codec and PCF8575 I2C GPIO expanders. **All libraries are included locally** - no global Arduino library dependencies required.


## Key Features

- **Completely Self-Contained**: All libraries included locally
- **Arduino Uno R4 WiFi Compatible**: Successfully compiles and runs
- **Hardware-Independent Button Mapping**: CSV-based configuration system
- **Multi-Press Support**: Playlist-driven audio sequences
- **Priority Modes**: Human-first vs Generated-first audio
- **Advanced Serial Interface**: Complete configuration and debugging commands
- **Real-time Calibration**: Interactive button mapping system


## Hardware Requirements

- **Arduino**: Uno/Nano/Mega (tested with Arduino Uno R4 WiFi)
- **Audio Codec**: Adafruit VS1053 Codec Breakout or Shield
- **GPIO Expanders**: Up to 3x PCF8575 I2C (addresses 0x20, 0x21, 0x22)
- **Storage**: MicroSD card (formatted as FAT32)
- **Buttons**: Up to 48 tactile buttons (via PCF8575) + 4 direct GPIO
- **Audio**: Speaker or headphones
- **Power**: 5V supply or rechargeable battery pack


## Pin Connections

### VS1053 Audio Codec

- **SHIELD_RESET**: Not connected (tied high on shield)
- **SHIELD_CS (xCS)**: Pin 7
- **SHIELD_DCS (xDCS)**: Pin 6
- **DREQ**: Pin 3 (INT1 on Uno)
- **CARDCS**: Pin 4 (micro-SD CS)

### PCF8575 I2C GPIO Expanders

- **SDA**: A4 (Uno) or dedicated SDA pin
- **SCL**: A5 (Uno) or dedicated SCL pin
- **VCC**: 5V
- **GND**: Ground
- **Addresses**: 0x20, 0x21, 0x22

### Direct GPIO Pins (Optional)

- **Pin 8**: Extra button input
- **Pin 9**: Extra button input
- **Pin 2**: Extra button input
- **Pin 5**: Extra button input


## Local Libraries Included

**No global library installation required!** All dependencies are included:

- **Adafruit_VS1053**: Audio codec control
- **Adafruit_PCF8575**: I2C GPIO expander (16-bit)
- **Adafruit_PCF8574**: I2C GPIO expander (8-bit)
- **Adafruit_BusIO_Register**: I2C/SPI register abstraction
- **Adafruit_I2CDevice**: I2C device handling
- **Adafruit_SPIDevice**: SPI device handling
- **Adafruit_GenericDevice**: Generic device abstraction


## Compilation Stats

- **Program Storage**: 93,936 bytes (35% of 262,144 bytes)
- **Dynamic Memory**: 12,788 bytes (39% of 32,768 bytes)
- **Target Platform**: Arduino Uno R4 WiFi 
- **Dependencies**: Zero global libraries required 


## SD Card Structure

```text
/
├── config/
│   ├── buttons.csv      # Hardware button mapping
│   ├── playlist.csv     # Audio playlist mapping
│   └── audio_index.csv  # Optional text descriptions
├── 01/ ... /33/         # TTS audio folders (1-33)
├── 101/ ... /133/       # REC audio folders (101-133)
└── audio files (.mp3)
```

## Button Calibration

The device includes a real-time calibration system:

1. **Enter Calibration Mode**: Send 'C' via serial
2. **Press Buttons**: Each press prompts for a label
3. **Assign Labels**: Type label and press Enter
4. **Save Configuration**: Send 'S' to save to SD card
5. **Exit**: Send 'E' to exit calibration mode

### Example Calibration Session

See `CALIBRATION_LOG.md` for a complete calibration session with 29 buttons mapped including letters A-Z, SPACE, PERIOD, YES, NO, WATER, and SHIFT.

## Serial Commands

- **C/c**: Enter calibration mode
- **E/e**: Exit calibration mode
- **S/s**: Save button mappings to SD
- **L/l**: Load configuration from SD
- **P/p**: Print current mappings
- **H/h**: Show help menu
- **M/m**: Toggle priority mode (HUMAN_FIRST/GENERATED_FIRST)
- **T/t**: Test all buttons with audio
- **U/u**: Check audio file sanity
- **V/v**: Show volume commands
- **+/-**: Volume control
- **1-9**: Set volume level (1=max, 9=quiet)
- **X/x**: Stop current audio playback

## Priority Modes

- **HUMAN_FIRST**: Prioritizes human recordings over TTS
- **GENERATED_FIRST**: Prioritizes TTS over human recordings
- **Toggle**: Triple-press the PERIOD button or use 'M' command

## Multi-Press Support

Each button supports multiple press sequences:
- **Single Press**: Plays first audio in sequence
- **Double Press**: Plays second audio in sequence
- **Triple Press**: Plays third audio in sequence
- **And so on...**

## Configuration Files

### buttons.csv
```csv
index,label
3,A
1,SHIFT
0,YES
25,NO
20,WATER
# ... more mappings
```

### playlist.csv
```csv
label,audio1,audio2,audio3
A,/01/001.mp3,/01/002.mp3,/01/003.mp3
WATER,/20/001.mp3,/20/002.mp3
# ... more playlists
```

## Usage

1. **Upload Sketch**: Compile and upload to Arduino Uno R4 WiFi
2. **Insert SD Card**: With proper folder structure and audio files
3. **Connect Hardware**: VS1053, PCF8575 expanders, buttons
4. **Power On**: Device initializes and shows status
5. **Calibrate**: Use 'C' command to map buttons
6. **Use**: Press buttons for audio playback

## Troubleshooting

### Compilation Issues
- **Fixed**: All libraries are local, no global conflicts
- **Fixed**: Arduino R4 WiFi compatibility issues resolved
- **Fixed**: PCF8575 method name conflicts resolved

### Hardware Issues
- **VS1053 Not Found**: Check SPI wiring and power
- **PCF8575 Not Detected**: Verify I2C connections and addresses
- **SD Card Issues**: Ensure FAT32 format and proper file structure
- **No Audio**: Check speaker connections and volume settings

### Button Issues
- **No Response**: Use calibration mode to map buttons
- **Wrong Audio**: Check playlist.csv configuration
- **Multiple Presses**: Adjust MULTI_PRESS_WINDOW timing

## Project History

This project evolved from a simple VS1053 audio player to a complete tactile communication device with:
- Hardware-independent button mapping
- Data-driven configuration system
- Local library integration for maximum compatibility
- Real-time calibration capabilities
- Advanced serial debugging interface

## License

Based on Adafruit's VS1053 and PCF8575 libraries. Released under the same license terms.

## Support

For hardware support:
- [Adafruit VS1053 Guide](https://learn.adafruit.com/adafruit-vs1053-mp3-aac-ogg-midi-wav-play-and-record-codec-tutorial)
- [Adafruit PCF8575 Guide](https://learn.adafruit.com/adafruit-pcf8575-i2c-16-gpio-expander) library integration.
