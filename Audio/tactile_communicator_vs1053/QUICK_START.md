# 🚀 QUICK START - VS1053 Tactile Communicator

## ⚡ 5-Minute Setup

### 1. Install Libraries (2 minutes)
Arduino IDE → Tools → Manage Libraries → Search & Install:
- **Adafruit VS1053 Library**
- **Adafruit PCF8575**

### 2. Upload Code (1 minute)
1. Open `tactile_communicator_vs1053.ino`
2. Select board: Tools → Board → Arduino Uno
3. Select port: Tools → Port → (your COM port)
4. Click Upload ⬆️

### 3. Load SD Card (1 minute)
Copy contents of `../SD_Structure/` to your SD card root

### 4. Test System (1 minute)
1. Open Serial Monitor (9600 baud)
2. Type `T` to test all buttons
3. Type `H` for help menu

---

## 🎵 Priority Audio Test

These buttons have your recorded voice:
- **A** (press once) → "Amer" [YOUR VOICE]
- **L** (press twice) → "I love you" [YOUR VOICE]  
- **D** (press once) → "Deen" [YOUR VOICE]
- **K** (press once) → "Kiyah" [YOUR VOICE]

---

## 🔌 Essential Connections

### VS1053 to Arduino:
```
VS1053    Arduino
------    -------
DREQ  →   Pin 3
CARDCS→   Pin 4  
DCS   →   Pin 6
CS    →   Pin 7
MOSI  →   Pin 11
MISO  →   Pin 12
SCK   →   Pin 13
5V    →   5V
GND   →   GND
```

### PCF8575 to Arduino:
```
PCF8575   Arduino
-------   -------
SDA   →   A4
SCL   →   A5
VCC   →   5V
GND   →   GND
```

---

## 🎮 Serial Commands

Type these in Serial Monitor:
- **`H`** → Help menu
- **`T`** → Test all buttons  
- **`C`** → Calibrate buttons
- **`E`** → Exit calibration
- **`+`** → Volume up
- **`-`** → Volume down
- **`s`** → Stop audio
- **`P`** → Print mappings
- **`S`** → Save config

---

## 🔧 Troubleshooting

**No audio?**
- Check SD card in VS1053
- Try `+` for volume up
- Type `T` to test

**Buttons not working?**
- Type `C` to calibrate
- Press buttons and assign labels
- Type `E` to exit

**Libraries missing?**
- Install Adafruit VS1053 Library
- Install Adafruit PCF8575
- Restart Arduino IDE

---

## ✅ Success Checklist

- [ ] Libraries installed
- [ ] Code uploads without errors
- [ ] Serial Monitor shows "VS1053 found"
- [ ] SD card initialized 
- [ ] PCF8575 chips online
- [ ] Audio test plays recorded words
- [ ] Buttons respond in calibration mode

**Ready to communicate!** 🎉

---

*For detailed instructions, see README.md, LIBRARIES.md, WIRING.md, and CONFIG.md*
