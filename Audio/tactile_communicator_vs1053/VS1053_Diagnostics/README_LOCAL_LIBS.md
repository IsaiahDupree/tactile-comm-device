# VS1053 Diagnostics - Local Libraries

This folder contains a completely self-contained VS1053 diagnostics sketch with all libraries included locally.

## Local Libraries Included:

### Core Libraries:
- **Adafruit_VS1053.h/cpp** - VS1053 audio codec library (Arduino Uno R4 WiFi compatible)
- **Adafruit_SPIDevice.h/cpp** - SPI device communication library
- **SD.h/cpp** - SD card library for file operations
- **File.cpp** - File handling utilities

### Utility Libraries:
- **utility/** folder - Contains SD card low-level utilities:
  - FatStructs.h - FAT filesystem structures
  - Sd2Card.h/cpp - SD card hardware interface
  - SdFat.h - FAT filesystem implementation
  - SdFile.cpp - File operations
  - SdVolume.cpp - Volume management
  - And more...

## Key Features:

### Enhanced Diagnostics:
- **Continuous status monitoring** every 2 seconds
- **Success beeps** when VS1053 is detected and working
- **Periodic test beeps** every 10 seconds to confirm ongoing functionality
- **Memory monitoring** and system status
- **DREQ pin monitoring** for connection diagnostics

### Arduino Uno R4 WiFi Compatibility:
- Fixed `sbrk` function compatibility issues
- Proper platform detection for memory management
- Renesas architecture support in VS1053 library

### No External Dependencies:
- All libraries are local - no Arduino Library Manager dependencies
- Uses local includes with double quotes: `#include "library.h"`
- Self-contained project folder

## Usage:

1. Open `VS1053_Diagnostics.ino` in Arduino IDE
2. Select your Arduino board (Uno, Uno R4 WiFi, etc.)
3. Upload the sketch
4. Open Serial Monitor at 115200 baud
5. Watch for continuous status reports and success beeps

## Expected Output:

**If VS1053 is working:**
- 3 loud success beeps on startup
- Status reports every 2 seconds showing "WORKING ✅"
- Periodic test beeps every 10 seconds
- Memory and uptime information

**If VS1053 is not working:**
- Status reports showing "NOT DETECTED ❌"
- Troubleshooting guidance
- DREQ pin status for wiring diagnosis

## Troubleshooting:

If compilation fails, ensure:
1. All files are in the same folder as the .ino file
2. Arduino IDE is using the local libraries (not global ones)
3. Board selection matches your hardware

## Hardware Connections:

- VS1053 VCC → Arduino 5V (or 3.3V for R4 WiFi)
- VS1053 GND → Arduino GND
- VS1053 MOSI → Arduino Pin 11
- VS1053 MISO → Arduino Pin 12
- VS1053 SCK → Arduino Pin 13
- VS1053 CS → Arduino Pin 10
- VS1053 DCS → Arduino Pin 8
- VS1053 DREQ → Arduino Pin 3
- VS1053 RST → Arduino Pin 9
- SD Card CS → Arduino Pin 4
