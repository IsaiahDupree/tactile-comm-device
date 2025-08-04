# Troubleshooting Guide

This guide helps resolve common issues with the tactile communication device.

## Quick Diagnostics

### Serial Monitor Check
1. Open Arduino IDE Serial Monitor (115200 baud)
2. Power on device
3. Look for initialization messages:

**✅ Good startup:**
```
TACTILE COMMUNICATION DEVICE - VS1053
[SUCCESS] VS1053 codec initialized successfully!
[SUCCESS] PCF8575 #0 (0x20) online - GPIO 0-15 ready
[SUCCESS] PCF8575 #1 (0x21) online - GPIO 16-31 ready
TACTILE COMMUNICATION DEVICE READY!
```

**❌ Problem indicators:**
- Missing VS1053 initialization
- PCF8575 not found warnings
- SD card initialization failed

## Common Issues & Solutions

### 🔇 No Audio Output

**Symptoms:**
- Device powers on but no sound
- Button presses detected but silent
- Serial shows audio commands but no playback

**Solutions:**

1. **Check Volume**
   ```
   Press '+' in Serial Monitor
   Try numbers 1-9 for different volume levels
   ```

2. **Verify Speaker Connections**
   - Right channel: VS1053 ROUT → Speaker +
   - Left channel: VS1053 LOUT → Speaker +  
   - Ground: VS1053 AGND → Speaker -

3. **Test VS1053 Audio**
   ```
   Press 'H' in Serial Monitor for menu
   Look for VS1053 sine wave test on startup
   ```

4. **Check Audio Files**
   - Verify MP3 files exist in correct folders
   - Test with known-good audio file
   - Ensure files are properly named (001.mp3, 002.mp3)

### 🔘 Buttons Not Responding

**Symptoms:**
- Pressing buttons shows no serial output
- Some buttons work, others don't
- Intermittent button detection

**Solutions:**

1. **Check I2C Connections**
   ```
   Look for these messages in serial:
   [SUCCESS] PCF8575 #0 (0x20) online
   [SUCCESS] PCF8575 #1 (0x21) online
   ```

2. **Verify STEMMA QT Cables**
   - Ensure cables are fully seated
   - Try different cable if available
   - Check for damaged connectors

3. **Test Individual Buttons**
   - Use multimeter to verify button continuity
   - Check that buttons connect GPIO pin to ground
   - Verify no stuck buttons

4. **I2C Address Conflicts**
   ```
   Default addresses: 0x20 and 0x21
   If conflicts, check other I2C devices
   ```

### 💾 SD Card Issues

**Symptoms:**
- "SD card initialization failed" error
- Audio files not found
- Config file not loading

**Solutions:**

1. **Format Requirements**
   - Use FAT32 file system only
   - 32GB or smaller capacity
   - Use official SD Card Formatter

2. **File Organization**
   ```
   Correct structure:
   /01/001.mp3, /01/002.mp3
   /05/001.mp3, /05/002.mp3
   config.csv (in root)
   
   Wrong:
   /1/1.mp3 (missing leading zeros)
   /01/001.wav (wrong format)
   ```

3. **File Naming**
   - Must use exactly 3 digits: 001.mp3, not 1.mp3
   - Folder names: 01, 02, not 1, 2
   - Case sensitive: .mp3, not .MP3

### ⚡ Power Problems

**Symptoms:**
- Device doesn't turn on
- Random resets
- Inconsistent operation

**Solutions:**

1. **Power Supply Check**
   - Use 5V USB-C supply with 2A+ capability
   - Avoid computer USB ports (often insufficient current)
   - Check for power LED on Arduino

2. **Wiring Issues**
   - Verify all connections are secure
   - Check for short circuits
   - Ensure proper gauge wire for button connections

### 🔧 Configuration Issues

**Symptoms:**
- Buttons mapped to wrong audio
- Calibration not saving
- Config file errors

**Solutions:**

1. **Manual Config Check**
   ```csv
   Correct config.csv format:
   index,label
   0,A
   1,B
   2,C
   ```

2. **Calibration Process**
   ```
   1. Press 'C' in Serial Monitor
   2. Press physical button
   3. Type label (e.g., "A")
   4. Press Enter
   5. Press 'E' to exit
   6. Press 'S' to save
   ```

3. **Load Config**
   ```
   Press 'L' to reload from SD card
   Check serial output for loading confirmations
   ```

## Diagnostic Commands

### Serial Monitor Commands

| Command | Function | Usage |
|---------|----------|-------|
| `H` | Show help menu | General navigation |
| `P` | Print button mappings | Check current configuration |
| `T` | Test all buttons | Verify audio files |
| `C` | Calibration mode | Assign button labels |
| `L` | Load config | Reload from SD card |
| `S` | Save config | Write to SD card |
| `+/-` | Volume control | Adjust audio level |
| `1-9` | Set volume level | Direct volume setting |
| `X` | Stop audio | Emergency audio stop |

### Hardware Test Sequence

1. **Power Test**
   - Connect USB-C power
   - Look for Arduino power LED
   - Open Serial Monitor @ 115200

2. **VS1053 Test**
   - Listen for brief sine wave on startup
   - Check for initialization success message

3. **I2C Test**
   - Verify PCF8575 detection messages
   - Both 0x20 and 0x21 should be found

4. **SD Card Test**
   - Insert properly formatted card
   - Check for successful initialization
   - Use 'L' command to test config loading

5. **Button Test**
   - Press 'C' for calibration mode
   - Press each button to verify detection
   - Check GPIO pin assignments in serial output

6. **Audio Test**
   - Use 'T' command to test all configured buttons
   - Verify audio playback for each button
   - Test volume controls

## Advanced Troubleshooting

### Hardware Debugging

**Multimeter Checks:**
- 5V power rail: Should measure ~5V
- 3.3V rail: Should measure ~3.3V
- Button continuity: 0Ω when pressed, open when released
- I2C lines: Should have pull-up voltage when idle

**Oscilloscope/Logic Analyzer:**
- I2C communication: 100kHz clock, proper start/stop
- SPI communication: VS1053 data transfer
- Audio output: Check for clean audio signals

### Software Debugging

**Enable Debug Mode:**
```cpp
// In firmware, set:
bool debugMode = true;
```

**Increase Logging:**
- Monitor multi-press timing
- Track audio file path resolution
- Watch I2C transaction details

### Component Substitution

**If Available:**
- Try different SD card
- Swap STEMMA QT cables
- Test with different speaker
- Use known-good PCF8575 modules

## Getting Help

### Information to Gather

When asking for help, include:

1. **Hardware Setup**
   - Arduino model and revision
   - Shield/breakout model
   - SD card brand and size
   - Number of buttons connected

2. **Software Information**
   - Arduino IDE version
   - Firmware version/commit
   - Library versions

3. **Serial Output**
   - Complete startup sequence
   - Error messages
   - Command responses

4. **Photos**
   - Wiring connections
   - Component layout
   - Any visible damage

### Where to Get Support

- **GitHub Issues**: Most technical problems
- **Arduino Forums**: General Arduino questions
- **Adafruit Forums**: Hardware-specific issues
- **Documentation**: Check all guides first

### Escalation Steps

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Try basic hardware tests
4. Gather diagnostic information
5. Create detailed issue report
6. Wait for community response

Remember: This device helps people communicate - community support is usually very responsive for accessibility projects! 🙏
