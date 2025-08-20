# Tactile Communication Device - Button Calibration Log

## Hardware Button Mapping (Calibrated)

This log shows the complete button calibration performed on the tactile communication device with VS1053 audio codec and PCF8575 I2C GPIO expanders.

### Calibration Session Results

```
*** CALIBRATION MODE ON ***
• Press any button to assign/update its label
• After press, type label and hit Enter
• Press 'E' to exit calibration

[BUTTON] PCF8575 #0 GPIO 3 → UNMAPPED | Press #1 @ 18844ms
Enter new label for index 3:
Mapped 3 → A

[BUTTON] PCF8575 #0 GPIO 1 → UNMAPPED | Press #1 @ 42660ms
Enter new label for index 1:
Mapped 1 → SHIFT

[BUTTON] PCF8575 #0 GPIO 0 → UNMAPPED | Press #1 @ 55397ms
Enter new label for index 0:
Mapped 0 → YES

[BUTTON] PCF8575 #1 GPIO 9 (idx 25) → UNMAPPED | Press #1 @ 61770ms
Enter new label for index 25:
Mapped 25 → NO

[BUTTON] PCF8575 #1 GPIO 4 (idx 20) → UNMAPPED | Press #1 @ 66364ms
Enter new label for index 20:
Mapped 20 → WATER

[BUTTON] PCF8575 #2 GPIO 3 (idx 35) → UNMAPPED | Press #1 @ 71911ms
Enter new label for index 35:
Mapped 35 → H

[BUTTON] PCF8575 #2 GPIO 1 (idx 33) → UNMAPPED | Press #1 @ 77231ms
Enter new label for index 33:
Mapped 33 → O

[BUTTON] PCF8575 #0 GPIO 13 → UNMAPPED | Press #1 @ 82874ms
Enter new label for index 13:
Mapped 13 → V

[BUTTON] PCF8575 #2 GPIO 2 (idx 34) → UNMAPPED | Press #1 @ 87318ms
Enter new label for index 34:
Mapped 34 → B

[BUTTON] PCF8575 #0 GPIO 8 → UNMAPPED | Press #1 @ 91010ms
Enter new label for index 8:
Mapped 8 → I

[BUTTON] PCF8575 #0 GPIO 5 → UNMAPPED | Press #1 @ 94898ms
Enter new label for index 5:
Mapped 5 → P

[BUTTON] PCF8575 #0 GPIO 11 → UNMAPPED | Press #1 @ 100631ms
Enter new label for index 11:
Mapped 11 → W

[BUTTON] PCF8575 #0 GPIO 14 → UNMAPPED | Press #1 @ 112801ms
Enter new label for index 14:
Mapped 14 → X

[BUTTON] PCF8575 #0 GPIO 10 → UNMAPPED | Press #1 @ 118415ms
Enter new label for index 10:
Mapped 10 → Q

[BUTTON] PCF8575 #0 GPIO 9 → UNMAPPED | Press #1 @ 122368ms
Enter new label for index 9:
Mapped 9 → J

[BUTTON] PCF8575 #0 GPIO 6 → UNMAPPED | Press #1 @ 126320ms
Enter new label for index 6:
Mapped 6 → C

[BUTTON] PCF8575 #1 GPIO 14 (idx 30) → UNMAPPED | Press #1 @ 134200ms
Enter new label for index 30:
Mapped 30 → D

[BUTTON] PCF8575 #0 GPIO 2 → UNMAPPED | Press #1 @ 140847ms
Enter new label for index 2:
Mapped 2 → K

[BUTTON] PCF8575 #0 GPIO 7 → UNMAPPED | Press #1 @ 147867ms
Enter new label for index 7:
Mapped 7 → R

[BUTTON] PCF8575 #1 GPIO 15 (idx 31) → UNMAPPED | Press #1 @ 154273ms
Enter new label for index 31:
Mapped 31 → Y

[BUTTON] PCF8575 #1 GPIO 12 (idx 28) → UNMAPPED | Press #1 @ 159408ms
Enter new label for index 28:
Mapped 28 → Z

[BUTTON] PCF8575 #1 GPIO 13 (idx 29) → UNMAPPED | Press #1 @ 165237ms
Enter new label for index 29:
Mapped 29 → S

[BUTTON] PCF8575 #1 GPIO 7 (idx 23) → UNMAPPED | Press #1 @ 168698ms
Enter new label for index 23:
Mapped 23 → L

[BUTTON] PCF8575 #1 GPIO 8 (idx 24) → UNMAPPED | Press #1 @ 177342ms
Enter new label for index 24:
Mapped 24 → E

[BUTTON] PCF8575 #1 GPIO 2 (idx 18) → UNMAPPED | Press #1 @ 181550ms
Enter new label for index 18:
Mapped 18 → F

[BUTTON] PCF8575 #1 GPIO 3 (idx 19) → UNMAPPED | Press #1 @ 185010ms
Enter new label for index 19:
Mapped 19 → M

[BUTTON] PCF8575 #1 GPIO 6 (idx 22) → UNMAPPED | Press #1 @ 188891ms
Enter new label for index 22:
Mapped 22 → T

[BUTTON] PCF8575 #1 GPIO 11 (idx 27) → UNMAPPED | Press #1 @ 193524ms
Enter new label for index 27:
Mapped 27 → SPACE

[BUTTON] PCF8575 #0 GPIO 15 → UNMAPPED | Press #1 @ 198187ms
Enter new label for index 15:
Mapped 15 → PERIOD

[BUTTON] PCF8575 #1 GPIO 5 (idx 21) → UNMAPPED | Press #1 @ 203946ms
Enter new label for index 21:
Mapped 21 → U

[BUTTON] PCF8575 #1 GPIO 0 (idx 16) → UNMAPPED | Press #1 @ 207496ms
Enter new label for index 16:
Mapped 16 → N

[BUTTON] PCF8575 #1 GPIO 1 (idx 17) → UNMAPPED | Press #1 @ 213693ms
Enter new label for index 17:
Mapped 17 → G

Config saved to config.csv
```

## Summary of Button Mappings

### PCF8575 #0 (GPIO 0-15)
- GPIO 0 → YES
- GPIO 1 → SHIFT  
- GPIO 2 → K
- GPIO 3 → A
- GPIO 5 → P
- GPIO 6 → C
- GPIO 7 → R
- GPIO 8 → I
- GPIO 9 → J
- GPIO 10 → Q
- GPIO 11 → W
- GPIO 13 → V
- GPIO 14 → X
- GPIO 15 → PERIOD

### PCF8575 #1 (GPIO 16-31, shown as idx 16-31)
- GPIO 0 (idx 16) → N
- GPIO 1 (idx 17) → G
- GPIO 2 (idx 18) → F
- GPIO 3 (idx 19) → M
- GPIO 4 (idx 20) → WATER
- GPIO 5 (idx 21) → U
- GPIO 6 (idx 22) → T
- GPIO 7 (idx 23) → L
- GPIO 8 (idx 24) → E
- GPIO 9 (idx 25) → NO
- GPIO 11 (idx 27) → SPACE
- GPIO 12 (idx 28) → Z
- GPIO 13 (idx 29) → S
- GPIO 14 (idx 30) → D
- GPIO 15 (idx 31) → Y

### PCF8575 #2 (GPIO 32-47, shown as idx 32-47)
- GPIO 1 (idx 33) → O
- GPIO 2 (idx 34) → B
- GPIO 3 (idx 35) → H

## Hardware Configuration
- **Arduino**: Uno R4 WiFi
- **Audio Codec**: Adafruit VS1053
- **GPIO Expanders**: 3x PCF8575 I2C (addresses 0x20, 0x21, 0x22)
- **Total Buttons Mapped**: 29 buttons
- **Date**: August 16, 2025
