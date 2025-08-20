# Required Library Installation Guide

## Critical Libraries (Must Install Before Compilation)

### 1. SdFat Library (v2.2.3+)
```
Arduino IDE → Tools → Manage Libraries → Search "SdFat" → Install latest version
```
**Required for:** SD card file operations, CSV parsing, audio file access

### 2. Adafruit PCF8575 Library
```
Arduino IDE → Tools → Manage Libraries → Search "Adafruit PCF8575" → Install
```
**Required for:** I2C port expander communication (button matrix)

### 3. Adafruit VS1053 Library
```
Arduino IDE → Tools → Manage Libraries → Search "Adafruit VS1053" → Install
```
**Required for:** Audio codec control and MP3 playback

## Hardware Configuration

### I2C Bus Setup
- **PCF8575 Expanders:** Connected to Wire1 bus (QT Py connector)
- **Addresses:** 0x20, 0x21, 0x22 (3 expanders total)
- **Total Buttons:** 48 expander pins + 4 Arduino pins = 52 buttons

### VS1053 Audio Shield Pins
- **Reset:** -1 (tied high on shield)
- **CS:** Pin 7
- **DCS:** Pin 6
- **DREQ:** Pin 3
- **SD CS:** Pin 4

## Compilation Checklist

1. ✅ Install SdFat library v2.2.3+
2. ✅ Install Adafruit PCF8575 library
3. ✅ Install Adafruit VS1053 library
4. ✅ Remove local SdFat.h and SdFat.cpp files
5. ✅ Fix duplicate Wire1.begin() calls
6. ✅ Update include statements to use library paths

## Post-Installation Verification

1. **Compile Test:** Sketch should compile without errors
2. **Library Paths:** Verify includes resolve to installed libraries
3. **I2C Scanner:** Run scanner to detect PCF8575 at 0x20, 0x21, 0x22
4. **SD Card Test:** Verify SD card mounts and files are accessible
5. **Audio Test:** VS1053 sine wave test should produce sound

## Common Issues

- **"SdFat.h not found":** Install SdFat library via Library Manager
- **"PCF8575 not found":** Check I2C wiring and addresses
- **"VS1053 not found":** Verify shield connections and power
- **Compilation errors:** Ensure all three libraries are installed
