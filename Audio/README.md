# Tactile Communication Device

A custom tactile communication device for accessible communication using large letter-shaped buttons and voice playback.

## 🎯 Project Overview

This device features:
- **32 tactile buttons**: 4 special buttons (Yes, No, Water, Aux) + 26 letters + Space + Period
- **Voice playback**: Natural-sounding female voice generated using ElevenLabs
- **Arduino-based**: Instant boot, low power, offline operation
- **Rechargeable battery**: Portable and reliable
- **3D printed enclosure**: PETG with raised tactile letters

## 📋 Letter-to-Words Assignments

### Special Buttons (Top Row)
- **YES** → "Yes"
- **NO** → "No"  
- **WATER** → "Water"
- **AUX** → "Hello How are You"

### Letters with Assigned Words
- **A** → Amer, Alari, Apple, Arabic Show
- **B** → Bathroom, Bye, Bed, Breathe, blanket
- **C** → Chair, car, Cucumber
- **D** → Deen, Daddy, Doctor, Door
- **F** → FaceTime, funny
- **G** → Good Morning, Go
- **H** → How are you, Heartburn
- **I** → Inside
- **K** → Kiyah, Kyan, Kleenex, Kaiser
- **L** → Lee, I love you, light down, light up
- **M** → Mohammad, Medicine, Medical
- **N** → Nada, Nadowie, Noah
- **O** → Outside
- **P** → Pain, Phone
- **R** → Room
- **S** → Scarf, Susu, Sinemet
- **T** → TV
- **U** → Urgent Care
- **W** → Water, Walker, wheelchair, walk

*Letters E, J, Q, V, X, Y, Z have no words currently assigned.*

## 🔧 Setup Instructions

### 1. Generate Audio Files

First, install Python dependencies:
```bash
pip install -r requirements.txt
```

Then generate all audio files using ElevenLabs:
```bash
python generate_audio.py
```

This will create:
- `11labs/special_buttons/` - Audio for Yes/No/Water/Aux buttons
- `11labs/letters/[a-z]/` - Audio for each letter's assigned words
- `11labs/punctuation/` - Audio for space and period
- `11labs/audio_index.json` - Complete mapping file

### 2. Prepare SD Card

1. Format a microSD card as FAT32
2. Create the following folder structure:
   ```
   SD_CARD/
   ├── 01/  (Special buttons: YES, NO, WATER, AUX)
   ├── 02/  (Letter A audio files)
   ├── 03/  (Letter B audio files)
   ...
   ├── 27/  (Letter Z audio files)
   └── 28/  (Punctuation: SPACE, PERIOD)
   ```
3. Copy the generated MP3 files to their corresponding folders
4. Rename files to sequential numbers (001.mp3, 002.mp3, etc.)

### 🔧 Hardware Assembly

#### Required Components:
- Arduino Uno/Nano (or compatible with I2C support)
- 2x PCF8575 I2C port expanders (addresses 0x20, 0x21)
- DFPlayer Mini MP3 module  
- MicroSD card (8GB or less, FAT32)
- 32+ tactile buttons
- 3W speaker (4-8 ohms)
- Rechargeable battery pack (7.4V Li-Po recommended)
- Pull-up resistors for I2C (4.7kΩ)

#### Wiring Diagram:
```
Arduino    PCF8575 #0 (0x20)    PCF8575 #1 (0x21)
5V     →   VCC                 VCC
GND    →   GND                 GND  
A4(SDA)→   SDA                 SDA
A5(SCL)→   SCL                 SCL

Arduino    DFPlayer Mini
5V     →   VCC
GND    →   GND
Pin 10 →   RX (DFPlayer)
Pin 11 →   TX (DFPlayer)
Pin 4  →   SD Card CS (if separate SD module)

DFPlayer Mini    Speaker
SPK_1        →   Speaker +
SPK_2        →   Speaker -

Buttons: Connect to PCF8575 GPIO pins 0-31
Extra controls: Arduino pins 8, 7, 0 (optional)
```

### 4. Arduino Programming

1. Install required libraries (see `arduino_libraries.txt`):
   - Adafruit_PCF8575
   - DFRobotDFPlayerMini  
   - SD, SPI, Wire, SoftwareSerial (usually pre-installed)
2. Open `tactile_communicator_pcf8575.ino` in Arduino IDE
3. Adjust I2C addresses if needed (default: 0x20, 0x21)
4. Upload to your Arduino

## 🎵 Voice Configuration

**Voice ID**: `RILOU7YmBhvwJGDGjNmP` (ElevenLabs)
**Model**: Eleven Monolingual v1
**Settings**: 
- Stability: 0.5
- Similarity Boost: 0.8
- Style: 0.2
- Speaker Boost: Enabled

## 🎮 Usage

### Single Press
Press any button once to hear the first assigned word/phrase.

### Multiple Presses
Press a button multiple times within 500ms to cycle through assigned words:
- 1st press → 1st word
- 2nd press → 2nd word
- etc.

### Examples:
- Press **L** once → "Lee"
- Press **L** twice quickly → "I love you"
- Press **L** three times quickly → "light down"
- Press **L** four times quickly → "light up"

## 📁 File Structure

```
Audio/
├── letter_mappings.json      # Word assignments configuration
├── generate_audio.py         # ElevenLabs audio generator
├── requirements.txt          # Python dependencies
├── tactile_communicator.ino  # Arduino code
├── README.md                # This file
└── 11labs/                  # Generated audio files
    ├── special_buttons/
    ├── letters/
    ├── punctuation/
    └── audio_index.json
```

## 🔧 Customization

### Adding New Words
1. Edit `letter_mappings.json`
2. Run `python generate_audio.py` to regenerate audio
3. Copy new files to SD card
4. Update Arduino code if needed

### Changing Voice Settings
Modify the `AUDIO_SETTINGS` in `generate_audio.py`:
```python
AUDIO_SETTINGS = {
    "stability": 0.5,      # 0.0 - 1.0
    "similarity_boost": 0.8, # 0.0 - 1.0
    "style": 0.2,          # 0.0 - 1.0
}
```

## 🔋 Power Management

- Device enters low-power mode when idle
- Battery indicator (optional LED)
- Estimated battery life: 8-12 hours continuous use
- Charging via USB-C (implementation dependent)

## 📞 Support

For technical support or modifications:
- Check connections if audio doesn't play
- Verify SD card formatting (FAT32, 8GB max)
- Ensure MP3 files are in correct folders
- Monitor serial output for debugging

## 🎁 Deliverables

- ✅ Fully assembled device
- ✅ Pre-loaded SD card with all audio
- ✅ Source code and documentation
- ✅ 3D print files (STL)
- ✅ Wiring diagrams
- ✅ Caregiver operation guide
- ✅ 1-year warranty and support

---

**Project Timeline**: Under 2 weeks once audio finalized
**Cost**: $600 including assembly and shipping to California
