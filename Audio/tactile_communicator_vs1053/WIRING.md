# Hardware Wiring Guide - VS1053 Tactile Communicator

## 🔌 Pin Connections

### VS1053 Codec Shield/Breakout ⭐ PRIMARY AUDIO
```
Arduino Uno    VS1053 Shield    Purpose
-----------    -------------    -------
5V         →   5V/VIN          Power
GND        →   GND             Ground
Pin 3      →   DREQ            Data Request (Interrupt)
Pin 4      →   CARDCS          SD Card Chip Select
Pin 6      →   SHIELD_DCS      Data Chip Select  
Pin 7      →   SHIELD_CS       Command Chip Select
Pin 11     →   MOSI            SPI Data Out
Pin 12     →   MISO            SPI Data In
Pin 13     →   SCK             SPI Clock
Audio Out  →   Speaker/Headphones
```

### PCF8575 I2C Port Expanders (Button Matrix)
```
Arduino     PCF8575 #0 (0x20)    PCF8575 #1 (0x21)    Purpose
-------     -----------------    -----------------    -------
5V      →   VCC                  VCC                  Power
GND     →   GND                  GND                  Ground
A4(SDA) →   SDA                  SDA                  I2C Data
A5(SCL) →   SCL                  SCL                  I2C Clock

Button Matrix:
PCF8575 #0 GPIO 0-15  → Buttons: YES, NO, WATER, AUX + Letters A-N
PCF8575 #1 GPIO 16-31 → Buttons: Letters O-Z + SPACE, PERIOD
```

### Optional Extra Controls
```
Arduino Pin    Purpose
-----------    -------
Pin 2      →   Extra button 34 (Volume/Power)
Pin 8      →   Extra button 32 (Reset/Menu)  
Pin 9      →   Extra button 33 (Test/Calibrate)
```

---

## 🔧 Detailed Connections

### VS1053 Shield Stacking (Easiest)
If using the **Adafruit VS1053 Shield**:
1. Stack directly onto Arduino Uno
2. All connections are automatic
3. SD card slot built-in
4. 3.5mm audio jack for headphones/speakers
5. Connect PCF8575 chips to shield's I2C pins

### VS1053 Breakout Wiring
If using the **VS1053 Breakout Board**:
```
Breakout Pin    Arduino Pin    Notes
------------    -----------    -----
MISO        →   12            SPI (shared with SD)
MOSI        →   11            SPI (shared with SD)  
SCK         →   13            SPI (shared with SD)
CS          →   7             VS1053 Command Select
DCS         →   6             VS1053 Data Select
DREQ        →   3             Interrupt pin
5V          →   5V            Power (or 3.3V if using 3.3V)
GND         →   GND           Ground
SDCS        →   4             SD Card Chip Select
```

### Button Wiring to PCF8575
```
Button Layout and GPIO Assignment:

Top Row (Special Buttons):
YES    → PCF8575 #0 GPIO 0
NO     → PCF8575 #0 GPIO 1  
WATER  → PCF8575 #0 GPIO 2
AUX    → PCF8575 #0 GPIO 3

Letters A-N:
A → GPIO 4    B → GPIO 5    C → GPIO 6    D → GPIO 7
E → GPIO 8    F → GPIO 9    G → GPIO 10   H → GPIO 11
I → GPIO 12   J → GPIO 13   K → GPIO 14   L → GPIO 15

Letters O-Z:
O → GPIO 16   P → GPIO 17   Q → GPIO 18   R → GPIO 19
S → GPIO 20   T → GPIO 21   U → GPIO 22   V → GPIO 23
W → GPIO 24   X → GPIO 25   Y → GPIO 26   Z → GPIO 27

Bottom Row:
SPACE  → GPIO 28
PERIOD → GPIO 29
(Reserved) → GPIO 30, 31
```

---

## 🔋 Power Requirements

### Power Consumption:
- Arduino Uno: ~50mA
- VS1053: ~40mA (playing) / ~15mA (idle)
- PCF8575 x2: ~1mA each
- Buttons: Negligible
- **Total**: ~100mA typical, 150mA peak

### Power Options:
1. **USB Power** (development/testing)
2. **9V Battery** with voltage regulator
3. **7.4V Li-Po** battery pack (recommended)
4. **5V Power Bank** (portable option)

---

## 🎵 Audio Output Options

### Built-in Options (VS1053 Shield):
- **3.5mm Headphone Jack** - Direct connection
- **Speaker Terminal** - Connect 4-8Ω speaker

### External Audio:
- **Powered Speakers** - Connect to headphone jack
- **Amplifier + Speaker** - For higher volume
- **Bluetooth Transmitter** - For wireless audio

---

## 🧪 Testing Setup

### Breadboard Testing (Recommended First):
1. **Arduino on breadboard** or development board
2. **VS1053 breakout** connected via jumper wires  
3. **Single PCF8575** for initial button testing
4. **Few buttons** connected to test basic functionality
5. **Small speaker** for audio verification

### Prototype Assembly:
1. Test all connections on breadboard first
2. Verify audio playback with SD card
3. Test button matrix scanning
4. Confirm I2C communication
5. Check power consumption

---

## ⚠️ Important Notes

### SPI Pin Conflicts:
- **VS1053 and SD card share SPI bus** - this is normal
- **Pin 11 used by both VS1053 and traditional SPI** - VS1053 code handles this
- **Don't use pins 3,4,6,7,11,12,13** for other purposes

### I2C Addresses:
- **PCF8575 #0**: 0x20 (default)
- **PCF8575 #1**: 0x21 (A0 pulled high)
- **Check your PCF8575 jumpers** match these addresses

### SD Card:
- **Format**: FAT32
- **Size**: ≤32GB recommended  
- **Files**: Use provided SD_Structure folder contents
- **Quality**: Use name-brand SD cards for reliability

---

## 🔧 Assembly Tips

### Order of Assembly:
1. **Test VS1053 alone** with working example code
2. **Add PCF8575 chips** and test I2C communication
3. **Connect a few buttons** and test button scanning
4. **Load SD card** with audio files and test playback
5. **Add remaining buttons** in groups
6. **Final integration** and testing

### Debugging Tools:
- **Serial Monitor** (9600 baud) for status messages
- **Multimeter** for power and continuity testing
- **Logic Analyzer** for I2C debugging (optional)
- **Oscilloscope** for SPI timing (optional)

Ready to wire up your professional-grade tactile communication device! 🎉
