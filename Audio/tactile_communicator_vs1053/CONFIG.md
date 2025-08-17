# Configuration and Calibration Guide

## 🚀 First Time Setup

### 1. Upload Code and Test
1. **Open Arduino IDE** and load `tactile_communicator_vs1053.ino`
2. **Select your board** (Tools → Board → Arduino Uno/Nano)
3. **Select COM port** (Tools → Port)
4. **Upload code** (Ctrl+U or Upload button)
5. **Open Serial Monitor** (Tools → Serial Monitor, 9600 baud)

### 2. Expected Startup Messages
```
Initializing Tactile Communication Device with VS1053...
VS1053 codec found.
SD card initialized.
VS1053 audio test...
Loading default mappings...
PCF8575 #0 (0x20) online.
PCF8575 #1 (0x21) online.
Testing audio system...
Playing startup audio...
=== Tactile Communication Device Ready ===
```

---

## 🎵 Audio System Testing

### Serial Commands for Testing:
```
H  → Show help menu
T  → Test all buttons automatically  
+  → Increase volume
-  → Decrease volume
X  → Stop current audio playback
P  → Print current button mappings
```

### Manual Audio Test:
1. Type `T` in Serial Monitor
2. Device will play each configured button's first track
3. Listen for clear audio quality
4. Verify recorded words sound natural
5. Check generated words are clear

---

## 🔘 Button Calibration

### Enter Calibration Mode:
1. Type `C` in Serial Monitor
2. You'll see: `*** CALIBRATION MODE ON ***`

### Calibrate Each Button:
1. **Press a button** on your device
2. Serial Monitor shows: `Button GPIO X pressed!`
3. **Type the button label** (e.g., "A", "YES", "WATER")
4. **Press Enter**
5. Device confirms: `Mapped X → LABEL`

### Example Calibration:
```
*** CALIBRATION MODE ON ***
Button GPIO 4 pressed!
Enter new label for index 4:
A
Mapped 4 → A

Button GPIO 0 pressed!  
Enter new label for index 0:
YES
Mapped 0 → YES
```

### Exit Calibration:
- Type `E` in Serial Monitor
- Returns to normal operation mode

---

## 💾 Configuration Management

### Save Button Mappings:
- Type `S` to save current mappings to SD card
- Creates/updates `config.csv` file
- Preserves your calibration between power cycles

### Load Saved Mappings:
- Type `L` to load mappings from SD card
- Automatically loads on startup if config.csv exists

### View Current Mappings:
- Type `P` to print all button assignments
- Shows GPIO number, label, folder, and track count

---

## 📁 SD Card Structure

### Required Folder Layout:
```
SD Card Root:
├── 01/          Special buttons (YES, NO, WATER, AUX)
│   ├── 001.mp3  "Yes" 
│   ├── 002.mp3  "No"
│   ├── 003.mp3  "Water"  
│   └── 004.mp3  "Hello How are You" [RECORDED]
├── 02/          Letter A
│   ├── 001.mp3  "Amer" [RECORDED]
│   ├── 002.mp3  "Alari" [RECORDED]
│   ├── 003.mp3  "Apple"
│   ├── 004.mp3  "Arabic Show"
│   └── 005.mp3  "Amory" [RECORDED]
├── 03/          Letter B  
│   ├── 001.mp3  "Bathroom"
│   ├── 002.mp3  "Bye" [RECORDED]
│   └── ...
└── config.csv   Button mappings (auto-generated)
```

### Copy SD Files:
Use the prepared `SD_Structure` folder from the main project:
```
Copy contents of: ../SD_Structure/*
To SD card root:  E:\ (or your SD drive)
```

---

## 🎯 Button Priority System

### Recorded Words (Priority):
These are your personal recordings that play in specific positions:
- **A (1st press)**: "Amer" [YOUR VOICE]
- **A (2nd press)**: "Alari" [YOUR VOICE]  
- **L (1st press)**: "Lee" [YOUR VOICE]
- **L (2nd press)**: "I love you" [YOUR VOICE]
- **D (1st press)**: "Deen" [YOUR VOICE]
- **D (2nd press)**: "Daddy" [YOUR VOICE]

### Multi-Press Operation:
- **Single press** → Play track 1
- **Double press** (quickly) → Play track 2
- **Triple press** (quickly) → Play track 3
- **Wait 0.5 seconds** between different buttons

---

## 🔧 Advanced Configuration

### Volume Adjustment:
```cpp
musicPlayer.setVolume(10, 10);  // Loud (0=loudest)
musicPlayer.setVolume(20, 20);  // Medium
musicPlayer.setVolume(40, 40);  // Quiet (100=mute)
```

### I2C Address Changes:
If you need different PCF8575 addresses:
```cpp
pcf0.begin(0x20, &Wire);  // Default address
pcf1.begin(0x21, &Wire);  // A0 high = +1
```

### Extra Pin Configuration:
```cpp
const uint8_t extraPins[] = { 8, 9, 2 };      // Physical pins
const uint8_t extraIndices[] = {32, 33, 34};  // Logical indices
```

---

## 🐛 Troubleshooting

### No Audio Output:
1. Check speaker/headphone connections
2. Try volume commands (`+` and `-`)
3. Verify SD card files exist
4. Test with `T` command

### Buttons Not Responding:
1. Enter calibration mode (`C`)
2. Press buttons and verify GPIO numbers
3. Check PCF8575 wiring and power
4. Verify I2C addresses (0x20, 0x21)

### SD Card Issues:
1. Format SD card as FAT32
2. Use ≤32GB SD card
3. Copy files from `SD_Structure` folder
4. Check file names match exactly (001.mp3, 002.mp3, etc.)

### Wrong Audio Playing:
1. Check folder structure matches button mappings
2. Verify track numbers (001.mp3 = 1st press, 002.mp3 = 2nd press)
3. Use `P` command to view current mappings
4. Recalibrate buttons if needed

---

## 📊 Status Monitoring

### Serial Monitor Output:
```
Button GPIO 4 (A) pressed! (Press #1)
Playing: A - /02/001.mp3
Audio playback finished

Button GPIO 4 (A) pressed! (Press #2)  
Playing: A - /02/002.mp3
Audio playback finished
```

### Health Checks:
- **VS1053 found**: Audio system working
- **SD card initialized**: File system ready  
- **PCF8575 online**: Button scanning active
- **Audio playback finished**: Normal operation

---

## ✅ Final Validation

### Complete System Test:
1. **Power on device** - Check startup messages
2. **Test special buttons** - YES, NO, WATER, AUX
3. **Test family names** - A (Amer), D (Deen), K (Kiyah), etc.
4. **Test multi-press** - L (Lee → I love you)
5. **Test volume** - Use +/- commands
6. **Save configuration** - Type `S` to preserve settings

### Ready for Production:
- ✅ All buttons respond correctly
- ✅ Audio quality is clear
- ✅ Recorded words play in priority positions  
- ✅ Multi-press cycling works smoothly
- ✅ Configuration saves/loads properly
- ✅ Device powers on reliably

**Your tactile communication device is ready for deployment! 🎉**
