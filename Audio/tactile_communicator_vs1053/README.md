# Tactile Communication Device - VS1053 Arduino Project

## 📁 Project Structure
This is a complete Arduino project for the tactile communication device using the VS1053 codec for superior audio quality.

## 🎯 Quick Start
1. **Open in Arduino IDE**: Open `tactile_communicator_vs1053.ino`
2. **Install Libraries**: See `LIBRARIES.md` for requirements
3. **Connect Hardware**: See `WIRING.md` for connections
4. **Upload Code**: Select your Arduino board and upload
5. **Load SD Card**: Copy audio files from `../SD_Structure/` to SD card

## 📋 Files in This Project

### Core Files:
- **`tactile_communicator_vs1053.ino`** - Main Arduino sketch
- **`LIBRARIES.md`** - Required library list and installation
- **`WIRING.md`** - Hardware connection diagrams
- **`CONFIG.md`** - Configuration and calibration guide

### Audio Files:
- Use SD card structure from `../SD_Structure/`
- 18 recorded personal words (priority)
- 37 generated words (ElevenLabs TTS)

## 🎵 VS1053 Benefits
- **Professional audio quality** vs. DFPlayer Mini
- **Reliable SD card handling**
- **Hardware interrupt support**
- **Better volume control**
- **Multiple audio format support**

## 🔧 Hardware Requirements
- Arduino Uno/Nano
- Adafruit VS1053 Codec Shield/Breakout
- 2x PCF8575 I2C Port Expanders
- 32+ Tactile Buttons
- MicroSD Card (FAT32, ≤32GB)
- Speaker or Headphones
- Power Supply

## 📞 Support
- Serial Monitor: 9600 baud for configuration and debugging
- Commands: H (help), T (test), C (calibrate), +/- (volume)

## 🚀 Status
✅ Code Complete  
✅ Audio Files Ready  
✅ Hardware Tested  
⏳ Final Assembly  

**Ready for production deployment!**
