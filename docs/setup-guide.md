# Setup Guide - Tactile Communication Device

This guide will walk you through setting up your tactile communication device from hardware assembly to software configuration.

## Prerequisites

- Basic electronics knowledge
- Arduino IDE installed
- Soldering equipment (if needed)
- MicroSD card (32GB or less, Class 10 recommended)

## Hardware Setup

### 1. Component Assembly

1. **Arduino Uno R4 WiFi** - Main controller
2. **VS1053 Music Maker Shield** - Mount on Arduino
3. **PCF8575 Expanders** - Connect via STEMMA QT cables
4. **Buttons** - Wire to PCF8575 GPIO pins
5. **Speaker** - Connect to VS1053 audio output
6. **Power** - USB-C connection

### 2. Wiring Connections

#### VS1053 Shield Connections (Auto-configured when mounted)
- RESET: Tied high on shield
- CS: Pin 7
- DCS: Pin 6
- DREQ: Pin 3
- SD CS: Pin 4

#### PCF8575 I2C Connections
- **PCF8575 #1 (0x20)**: STEMMA QT connector
- **PCF8575 #2 (0x21)**: Daisy-chain via STEMMA QT

#### Button Wiring
- Connect buttons between PCF8575 GPIO pins and ground
- Internal pull-ups are enabled in software
- Buttons 0-15: PCF8575 #1
- Buttons 16-31: PCF8575 #2

### 3. Power Requirements
- 5V USB-C power supply
- Minimum 2A current capability
- Power LED should illuminate when connected

## Software Setup

### 1. Arduino IDE Configuration

1. Install Arduino IDE 2.0+
2. Add Arduino Uno R4 WiFi board support:
   - Go to **Tools → Board → Boards Manager**
   - Search "Arduino UNO R4 WiFi"
   - Install the latest version

### 2. Required Libraries

Install these libraries via **Tools → Manage Libraries**:

- `Adafruit VS1053 Library`
- `Adafruit PCF8575 Library`
- `Adafruit BusIO Library`
- `SD Library` (built-in)

### 3. Upload Firmware

1. Open `/firmware/tactile_comm_device_vs1053/tactile_comm_device_vs1053.ino`
2. Select **Tools → Board → Arduino UNO R4 WiFi**
3. Select correct COM port under **Tools → Port**
4. Click **Upload** button
5. Wait for "Upload complete" message

## SD Card Setup

### 1. Format SD Card
- Use FAT32 file system
- 32GB or smaller recommended
- Use official SD Card Formatter tool

### 2. Audio File Structure

Create numbered folders on SD card root:
```
/01/    - Special buttons (YES, NO, WATER, HELP)
/05/    - Letter A variations
/06/    - Letter B variations
...
/30/    - Letter Z variations
/31/    - SPACE button
/32/    - PERIOD button
/33/    - SHIFT/HELP system
```

### 3. Audio File Naming

Files within each folder:
```
001.mp3 - First press audio
002.mp3 - Second press audio
003.mp3 - Third press audio
...
```

### 4. Configuration File

Create `config.csv` in SD card root:
```csv
index,label
0,A
1,B
2,C
...
```

## Initial Testing

### 1. Power On Test

1. Insert programmed SD card
2. Connect USB-C power
3. Open Arduino Serial Monitor (115200 baud)
4. Look for initialization messages

### 2. Hardware Verification

Expected serial output:
```
TACTILE COMMUNICATION DEVICE - VS1053
[SUCCESS] VS1053 codec initialized successfully!
[SUCCESS] PCF8575 #0 (0x20) online - GPIO 0-15 ready
[SUCCESS] PCF8575 #1 (0x21) online - GPIO 16-31 ready
```

### 3. Button Testing

1. Press 'T' in serial monitor to test all buttons
2. Each configured button should play its audio
3. Check for proper button detection in serial log

### 4. Volume Control

- Press '+' or '-' in serial monitor
- Use numbers 1-9 for specific volume levels
- 1 = maximum volume, 9 = quietest

## Configuration Commands

Open Serial Monitor (115200 baud) and use these commands:

- `C` - Enter calibration mode
- `E` - Exit calibration mode  
- `P` - Print current button mappings
- `L` - Load configuration from SD card
- `S` - Save current configuration to SD card
- `T` - Test all configured buttons
- `+/-` - Volume up/down
- `1-9` - Set specific volume level
- `X` - Stop current audio playback
- `H` - Show help menu

## Calibration Process

1. Enter calibration mode with 'C'
2. Press any button you want to configure
3. Type the label (e.g., "A", "HELP", "WATER")
4. Press Enter to confirm
5. Repeat for all buttons
6. Press 'E' to exit calibration
7. Press 'S' to save configuration

## Troubleshooting

### Common Issues

**No audio output:**
- Check speaker connections
- Verify VS1053 shield mounting
- Test volume with '+' command

**Buttons not responding:**
- Check PCF8575 I2C connections
- Verify STEMMA QT cable connections
- Look for I2C address conflicts in serial log

**SD card errors:**
- Reformat as FAT32
- Check file/folder naming
- Ensure 32GB or smaller capacity

**Power issues:**
- Use 2A+ USB-C power supply
- Check all connections
- Verify Arduino power LED

### Getting Help

Check the serial monitor output for detailed error messages. The device provides extensive logging to help diagnose issues.

For additional support, see the troubleshooting guide or submit an issue on the GitHub repository.
