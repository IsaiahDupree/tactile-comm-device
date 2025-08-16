# Tactile Communication Device Firmware

This directory contains multiple firmware variants for the tactile communication device, each optimized for different use cases and development stages.

## Firmware Variants

### 1. `tactile-comm-self-contained/` ⭐ **RECOMMENDED FOR PRODUCTION**
**Complete self-contained build with zero global Arduino library dependencies**

- **Target**: Arduino Uno R4 WiFi (Renesas architecture compatible)
- **Features**: Full tactile communication device with VS1053 audio codec and PCF8575 I2C GPIO expanders
- **Libraries**: All Adafruit libraries included locally (VS1053, BusIO suite, PCF8575)
- **Dependencies**: None - completely portable and self-contained
- **Compilation**: 93,936 bytes (35% program storage), 12,788 bytes (39% dynamic memory)
- **Status**: ✅ Production ready, fully tested

**Key Benefits:**
- Zero global library dependencies
- Platform compatibility fixes for Arduino Uno R4 WiFi
- All includes use local double-quote format
- Complete hardware independence via CSV configuration
- Supports up to 3 PCF8575 expanders (48 buttons + 4 GPIO = 52 total)

### 2. `tactile-comm-data-driven/`
**CSV-driven hardware and content mapping system**

- **Target**: Arduino Uno R4 WiFi
- **Features**: Hardware-software decoupling via CSV configuration files
- **Configuration**: `config/buttons.csv` for GPIO mapping, `config/playlist.csv` for content
- **Benefits**: Hardware changes only require CSV updates, no code recompilation
- **Status**: ✅ Fully functional with local libraries

### 3. `player_simple_working_directory_v2/` (Legacy)
**Earlier version of self-contained build**

- **Status**: Superseded by `tactile-comm-self-contained/`
- **Note**: Kept for historical reference

### 4. `tactile_comm_device_vs1053/` (Legacy)
**Original implementation**

- **Status**: Legacy version
- **Note**: May have global library dependencies

### 5. `vs1053_player_simple/` (Legacy)
**Basic VS1053 player example**

- **Status**: Simple example for testing VS1053 functionality

## Quick Start

### For Production Deployment:
```bash
cd tactile-comm-self-contained/
# Open tactile_communicator_working_directory.ino in Arduino IDE
# Select board: Arduino Uno R4 WiFi
# Compile and upload
```

### For Development/Customization:
```bash
cd tactile-comm-data-driven/
# Modify config/buttons.csv for hardware changes
# Modify config/playlist.csv for content changes
# No code recompilation needed
```

## Hardware Requirements

- **Arduino Uno R4 WiFi** (Renesas architecture)
- **Adafruit VS1053 Audio Codec** (SPI)
- **PCF8575 I2C GPIO Expanders** (1-3 units, up to 48 buttons)
- **SD Card** (FAT32, for audio files and configuration)
- **Buttons** (momentary push buttons)
- **Audio Output** (headphones, speaker, or amplifier)

## Pin Connections

See individual firmware README files for specific pin connection diagrams.

## Compilation Requirements

- **Arduino IDE** 1.8.x or 2.x
- **Board Package**: Arduino Renesas UNO R4 Boards
- **No external libraries required** (all included locally)

## SD Card Structure

Each firmware variant may use different SD card structures. See:
- `/sd/SD_FUTURE_PROOF/` for the recommended future-proof structure
- Individual firmware README files for specific requirements

## Documentation

- `tactile-comm-self-contained/README.md` - Complete setup and usage guide
- `tactile-comm-self-contained/CALIBRATION_LOG.md` - Button calibration reference
- `/docs/` - Additional documentation and guides

## Support

For issues, feature requests, or contributions, please refer to the main repository documentation.
