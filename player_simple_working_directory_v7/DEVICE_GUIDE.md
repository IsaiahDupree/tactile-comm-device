# Tactile Communication Device - User Guide

## Table of Contents
1. [Device Overview](#device-overview)
2. [Getting Started](#getting-started)
3. [Basic Operation](#basic-operation)
4. [Button Mapping Reference](#button-mapping-reference)
5. [SD Card Management](#sd-card-management)
6. [Audio File Organization](#audio-file-organization)
7. [Software Updates](#software-updates)
8. [Hardware Maintenance](#hardware-maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Complete Word List](#complete-word-list)

---

## Device Overview

The Tactile Communication Device is an assistive technology tool designed to help users communicate through pre-recorded audio messages. The device features:

- **26 Letter Buttons (A-Z)**: For spelling and word selection
- **Special Function Buttons**: SHIFT, PERIOD, SPACE, YES, NO, WATER
- **Multi-Press Support**: Press buttons multiple times for different audio options
- **Dual Audio Banks**: Human-recorded and computer-generated speech
- **SD Card Storage**: Expandable audio library
- **USB Connectivity**: For programming and file management

---

## Getting Started

### Initial Setup

1. **Power Connection**: Connect the device via USB cable to power source
2. **SD Card**: Ensure SD card is properly inserted (contains audio files and configuration)
3. **Serial Monitor**: Open Arduino IDE Serial Monitor at 115200 baud to see device status
4. **Audio Output**: Connect speakers or headphones to audio jack

### First Boot

When powered on, the device will:
1. **5-second initialization delay** - Device is loading and configuring
2. **Startup beep** - Confirms successful boot
3. Display status messages:
```
=== Tactile Communication Device - New SD Structure ===
[CONFIG] Loading button mappings from /CONFIG/KEYS.CSV
[CONFIG] Loaded X button mappings
[AUDIO] Ready for communication
```

**Note**: Wait for the startup beep before using the device buttons.

---

## Basic Operation

### Single Button Press
- Press any letter button (A-Z) to play the first audio file for that letter
- Press special buttons (YES, NO, WATER) for immediate responses

### Multi-Press Feature
- Press the same button multiple times within 1 second for different audio options
- Example: Press "A" twice quickly to access the second audio file for letter A

### SHIFT Button Functions
- **Press 1x**: Human greeting ("Hello, how are you?")
- **Press 2x**: Device instructions (computer-generated)
- **Press 3x**: Complete word list and button mapping (computer-generated)
- **Press 4x+**: Additional instructional content if available

### PERIOD Button Functions
- **Press 1x**: Period punctuation sound
- **Press 2x**: Switch to Human-First mode (prioritizes human-recorded audio)
- **Press 3x**: Switch to Generated-First mode (prioritizes computer-generated audio)
- **Press 4x**: Enter calibration mode (advanced users only)

---

## Button Mapping Reference

### Letters A-Z
Each letter button corresponds to its respective letter and associated words/phrases.

### Special Buttons
| Button | Function | Location |
|--------|----------|----------|
| SHIFT | Instructions/Greetings | Top row |
| YES | Affirmative response | Top row |
| NO | Negative response | Top row |
| WATER | Request for water | Top row |
| PERIOD | Punctuation/Mode switching | Bottom area |
| SPACE | Word spacing | Bottom area |

### Hardware Button Layout
```
[SHIFT] [YES] [NO] [WATER]

[A] [B] [C] [D] [E] [F] [G]
[H] [I] [J] [K] [L] [M] [N]
[O] [P] [Q] [R] [S] [T] [U]
[V] [W] [X] [Y] [Z]

[SPACE] [PERIOD]
```

---

## SD Card Management

### Accessing the SD Card

**SD Card Access Method:**
1. Power off the device
2. Gently remove SD card from slot
3. Insert into computer's SD card reader
4. Make changes to files
5. Safely eject and reinsert into device

### SD Card Structure
```
SD_CARD/
├── CONFIG/
│   └── KEYS.CSV          # Button mapping configuration
├── AUDIO/
│   ├── HUMAN/            # Human-recorded audio files
│   │   ├── A/            # Letter A audio files
│   │   ├── B/            # Letter B audio files
│   │   ├── ...           # (All letters A-Z)
│   │   ├── SHIFT/        # SHIFT button audio
│   │   ├── YES/          # YES button audio
│   │   ├── NO/           # NO button audio
│   │   ├── WATER/        # WATER button audio
│   │   └── PERIOD/       # PERIOD button audio
│   └── GENERA~1/         # Computer-generated audio files
│       ├── A/            # Letter A generated audio
│       ├── B/            # Letter B generated audio
│       ├── ...           # (All letters A-Z)
│       └── SHIFT/        # SHIFT instructions/word list
```

---

## Audio File Organization

### File Naming Convention
- **Audio Files**: `001.MP3`, `002.MP3`, `003.MP3`, etc.
- **Description Files**: `001.TXT`, `002.TXT`, `003.TXT`, etc.
- **Playlist Files**: `PLAYLIST.M3U` (auto-generated)

### Important: SdFat Library Naming Limitations

The device uses the SdFat library which has specific file and folder naming restrictions:

**Folder Name Restrictions:**
- **Maximum 8 characters** for folder names (8.3 format)
- **No spaces** in folder names
- **GENERATED folder** appears as `GENERA~1` due to length limit
- Use **UPPERCASE** letters for consistency

**File Name Restrictions:**
- **8.3 format**: Maximum 8 characters + 3-character extension
- **Examples**: `001.MP3`, `002.TXT`, `PLAYLIST.M3U`
- **Avoid long filenames** - they may be truncated or cause errors

**Recommended Naming:**
- Folders: `A`, `B`, `C`, `HUMAN`, `GENERA~1`, `CONFIG`
- Audio files: `001.MP3`, `002.MP3`, `003.MP3`
- Text files: `001.TXT`, `002.TXT`, `003.TXT`

**What Happens with Long Names:**
- Long folder names get truncated (e.g., `GENERATED` → `GENERA~1`)
- Files with long names may not be recognized by the device
- Spaces in names can cause file access issues

### Adding New Audio Files

1. **Record Audio**: Create MP3 files (recommended: 22kHz, mono, 64kbps)
2. **Name Files**: Use sequential numbers (001.MP3, 002.MP3, etc.)
3. **Create Descriptions**: Add matching .TXT files with content descriptions
4. **Choose Bank**: Place in either HUMAN/ or GENERA~1/ directory
5. **Select Letter**: Place in appropriate letter subdirectory (A/, B/, etc.)

### Example File Structure for Letter "A"
```
AUDIO/HUMAN/A/
├── 001.MP3              # "Apple"
├── 001.TXT              # "Apple - red fruit"
├── 002.MP3              # "Ambulance"
├── 002.TXT              # "Ambulance - emergency vehicle"
└── PLAYLIST.M3U         # Auto-generated playlist
```

---

## Software Updates

### Prerequisites
- Arduino IDE installed on computer
- USB cable for device connection
- Complete project folder downloaded to your computer
- Device firmware files (.ino)

### Download and Setup Project

1. **Download Project Folder**
   - Download the complete project folder (e.g., `player_simple_working_directory_v6`)
   - Extract/save to a location like: `C:\Users\[YourName]\Documents\Arduino\player_simple_working_directory_v6`
   - **Important**: The folder must contain all files including the .ino file and supporting libraries

2. **Verify Project Structure**
   - Ensure the folder contains:
     - `player_simple_working_directory_v6.ino` (main firmware file)
     - Supporting library folders (e.g., `Adafruit_BusIO`, `SdFat-2.2.3`)
     - `SD_CARD_STRUCTURE` folder with sample files
     - Python upload scripts

### Update Process

1. **Connect Device**
   - Connect via USB cable
   - Note the COM port (e.g., COM5)

2. **Open Arduino IDE**
   - Launch Arduino IDE
   - Navigate to your project folder
   - Open the firmware file: `player_simple_working_directory_v6.ino`
   - **Critical**: The .ino file must be opened from within its project folder

3. **Configure Arduino IDE**
   - Select Board: "Arduino UNO R4 WiFi" (or your specific model)
   - Select Port: Choose the correct COM port
   - Set Baud Rate: 115200

4. **Upload Firmware**
   - Click "Upload" button (arrow icon)
   - Wait for "Done uploading" message
   - Device will automatically restart

5. **Verify Update**
   - Open Serial Monitor (115200 baud)
   - Look for startup messages confirming successful boot

### Backup Before Updates
- Always backup your SD card files before firmware updates
- Note current button configuration in case reset is needed

---

## Hardware Maintenance

### Opening the Device

**Tools Required:**
- M3 hex screwdriver (Allen key)
- Anti-static wrist strap (recommended)

**Steps:**
1. **Power Off**: Disconnect USB cable and ensure device is off
2. **Remove Screws**: Use M3 hex screwdriver to remove case screws
3. **Lift Top**: Carefully lift the top cover
4. **Access Components**: SD card slot, Arduino board, and wiring are now accessible

### SD Card Replacement
1. Open device case (see above)
2. Gently push SD card to eject from slot
3. Insert new SD card with proper file structure
4. Reassemble device

### Cleaning
- **Buttons**: Use alcohol wipes on button surfaces
- **Case**: Clean with damp cloth, avoid water near openings
- **Contacts**: Use compressed air for dust removal

### Reassembly
1. Ensure all cables are properly connected
2. Check SD card is fully inserted
3. Replace top cover carefully
4. Reinstall M3 screws (don't overtighten)
5. Test device before returning to service

---

## Troubleshooting

### Common Issues

**Device Won't Turn On**
- Check USB cable connection
- Try different USB port or power adapter
- Verify cable integrity

**No Audio Output**
- Check speaker/headphone connection
- Verify audio files exist on SD card
- Test with known working audio files

**Buttons Not Responding**
- Check Serial Monitor for button press detection
- Verify button mapping in KEYS.CSV
- Consider recalibration if needed

**SD Card Not Recognized**
- Ensure SD card is properly inserted
- Check SD card format (FAT32 recommended)
- Try different SD card

**Garbled Audio**
- Check audio file format (MP3 recommended)
- Verify file isn't corrupted
- Check sample rate and bitrate

**Files Not Found/Not Playing**
- Verify file names follow 8.3 format (max 8 chars + extension)
- Check folder names are 8 characters or less
- Ensure no spaces in file or folder names
- Confirm files are in correct directory structure

### Serial Commands for Diagnostics

Connect via Serial Monitor (115200 baud) and use these commands:

- `S` - Show device status
- `L` - List SD card contents
- `M` - Toggle audio mode (Human/Generated priority)
- `C` - Enter calibration mode
- `H` - Show help menu

---

## Complete Word List

### SHIFT Button Audio Content

**Press 1x - Human Greeting**
- "Hello, how are you? I'm using this device to communicate with you."

**Press 2x - Comprehensive Guide**
- A comprehensive guide for users to understand how to use the device and interpret button presses

**Press 3x - Complete Button Mapping**
- Full audio description of all button functions and available words

### Complete Button Mapping Reference

Each letter contains multiple audio options accessible through multi-press:

**Letter A** (Hardware: pcf0:03)
- Press 1x: "Apple"
- Press 2x: "Ambulance" 
- Press 3x: "Attention"
- Press 4x+: Additional options if available

**Letter B** (Hardware: pcf2:08)
- Press 1x: "Bathroom"
- Press 2x: "Bed"
- Press 3x: "Blanket"
- Press 4x+: Additional options if available

**Letter C** (Hardware: pcf0:06)
- Press 1x: "Call"
- Press 2x: "Cold"
- Press 3x: "Comfortable"
- Press 4x+: Additional options if available

**Letter D** (Hardware: pcf1:14)
- Press 1x: "Doctor"
- Press 2x: "Drink"
- Press 3x: "Done"
- Press 4x+: Additional options if available

**Letter E** (Hardware: pcf1:08)
- Press 1x: "Emergency"
- Press 2x: "Eat"
- Press 3x: "Excuse me"
- Press 4x+: Additional options if available

**Letter F** (Hardware: pcf1:02)
- Press 1x: "Food"
- Press 2x: "Family"
- Press 3x: "Finished"
- Press 4x+: Additional options if available

**Letter G** (Hardware: pcf1:01)
- Press 1x: "Good"
- Press 2x: "Go"
- Press 3x: "Get"
- Press 4x+: Additional options if available

**Letter H** (Hardware: pcf2:09)
- Press 1x: "Help"
- Press 2x: "Hot"
- Press 3x: "Hurt"
- Press 4x+: Additional options if available

**Letter I** (Hardware: pcf0:08)
- Press 1x: "I"
- Press 2x: "Ice"
- Press 3x: "Important"
- Press 4x+: Additional options if available

**Letter J** (Hardware: pcf0:09)
- Press 1x: "Just"
- Press 2x: "Juice"
- Press 3x: "Jump"
- Press 4x+: Additional options if available

**Letter K** (Hardware: pcf0:02)
- Press 1x: "Keep"
- Press 2x: "Know"
- Press 3x: "Kind"
- Press 4x+: Additional options if available

**Letter L** (Hardware: pcf1:07)
- Press 1x: "Light"
- Press 2x: "Look"
- Press 3x: "Listen"
- Press 4x+: Additional options if available

**Letter M** (Hardware: pcf1:03)
- Press 1x: "Medicine"
- Press 2x: "More"
- Press 3x: "Move"
- Press 4x+: Additional options if available

**Letter N** (Hardware: pcf1:00)
- Press 1x: "Nurse"
- Press 2x: "Need"
- Press 3x: "Now"
- Press 4x+: Additional options if available

**Letter O** (Hardware: pcf2:13)
- Press 1x: "Okay"
- Press 2x: "Open"
- Press 3x: "Out"
- Press 4x+: Additional options if available

**Letter P** (Hardware: pcf0:05)
- Press 1x: "Pain"
- Press 2x: "Please"
- Press 3x: "Pillow"
- Press 4x+: Additional options if available

**Letter Q** (Hardware: pcf0:10)
- Press 1x: "Question"
- Press 2x: "Quiet"
- Press 3x: "Quick"
- Press 4x+: Additional options if available

**Letter R** (Hardware: pcf0:07)
- Press 1x: "Rest"
- Press 2x: "Room"
- Press 3x: "Ready"
- Press 4x+: Additional options if available

**Letter S** (Hardware: pcf1:13)
- Press 1x: "Stop"
- Press 2x: "Sleep"
- Press 3x: "Sit"
- Press 4x+: Additional options if available

**Letter T** (Hardware: pcf1:06)
- Press 1x: "Thank you"
- Press 2x: "Time"
- Press 3x: "Toilet"
- Press 4x+: Additional options if available

**Letter U** (Hardware: pcf1:05)
- Press 1x: "Urgent"
- Press 2x: "Up"
- Press 3x: "Understand"
- Press 4x+: Additional options if available

**Letter V** (Hardware: pcf0:13)
- Press 1x: "Very"
- Press 2x: "Visit"
- Press 3x: "Voice"
- Press 4x+: Additional options if available

**Letter W** (Hardware: pcf0:11)
- Press 1x: "Water"
- Press 2x: "Wait"
- Press 3x: "Want"
- Press 4x+: Additional options if available

**Letter X** (Hardware: pcf0:14)
- Press 1x: "X-ray"
- Press 2x: "Exit"
- Press 3x: "Extra"
- Press 4x+: Additional options if available

**Letter Y** (Hardware: pcf1:15)
- Press 1x: "Yes"
- Press 2x: "You"
- Press 3x: "Yesterday"
- Press 4x+: Additional options if available

**Letter Z** (Hardware: pcf1:12)
- Press 1x: "Zero"
- Press 2x: "Zone"
- Press 3x: "Zip"
- Press 4x+: Additional options if available

### Special Function Buttons

**SHIFT Button** (Hardware: pcf0:01)
- Press 1x: "Hello, how are you? I'm using this device to communicate with you."
- Press 2x: Device instructions and usage guide
- Press 3x: Complete button mapping and word list
- Press 4x+: Additional instructional content

**YES Button** (Hardware: pcf0:00)
- Press 1x: "Yes"
- Press 2x: "Okay" 
- Press 3x: "Correct"
- Press 4x: "I agree"

**NO Button** (Hardware: pcf1:09)
- Press 1x: "No"
- Press 2x: "Stop"
- Press 3x: "Incorrect"
- Press 4x: "I disagree"

**WATER Button** (Hardware: pcf1:04)
- Press 1x: "Water please"
- Press 2x: "I'm thirsty"
- Press 3x: "Drink"
- Press 4x+: Additional drink-related phrases

**SPACE Button** (Hardware: pcf1:11)
- Press 1x: Word spacing sound
- Press 2x+: Additional spacing options

**PERIOD Button** (Hardware: pcf0:15)
- Press 1x: Period punctuation sound
- Press 2x: Switch to Human-First mode
- Press 3x: Switch to Generated-First mode
- Press 4x: Enter calibration mode (advanced users)

### Quick Reference - Emergency Communications

**Immediate Emergency Access:**
- **U (Press 1x)**: "Urgent" - Immediate attention needed
- **H (Press 1x)**: "Help" - Request assistance
- **P (Press 1x)**: "Pain" - Indicate discomfort
- **E (Press 1x)**: "Emergency" - Critical situation
- **D (Press 1x)**: "Doctor" - Request medical professional
- **N (Press 1x)**: "Nurse" - Request nursing assistance

**Common Needs:**
- **W (Press 1x)**: "Water" - Request hydration
- **T (Press 3x)**: "Toilet" - Bathroom needs
- **M (Press 1x)**: "Medicine" - Medication request
- **B (Press 1x)**: "Bathroom" - Restroom needs
- **F (Press 1x)**: "Food" - Nutrition request

---

## Support and Maintenance Schedule

### Daily Checks
- Verify device powers on properly
- Test basic button functionality
- Check audio output quality

### Weekly Maintenance
- Clean button surfaces
- Check SD card security
- Verify all audio files play correctly

### Monthly Review
- Update audio content as needed
- Review button mapping effectiveness
- Check for firmware updates

### Contact Information
For technical support or questions about device operation, consult with your device administrator or technical support team familiar with Arduino-based assistive technology.

---

*Document Version: 1.0*  
*Last Updated: January 2025*  
*Compatible with: Tactile Communication Device v6*
