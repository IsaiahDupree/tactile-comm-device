# Arduino SD Loader Utility

This utility lets you load the `sd/SD_FUTURE_PROOF/` folder onto an SD card mounted on an Arduino (e.g., VS1053 shield + SD) via serial, without removing the SD card.

## Contents

- `ArduinoSDLoader/ArduinoSDLoader.ino` — Firmware exposing a simple serial protocol to read/write SD.
- `python_uploader.py` — Desktop script that syncs files to SD over serial.
- `lib/` — Placeholder for any third-party libraries (usually not needed; `SD` and `SPI` are built-in with the Arduino IDE).

## Hardware/Library Requirements

- Arduino with SD card slot (e.g., UNO + VS1053 MP3 shield with SD)
- SD wired to SPI; set the correct CS pin in the sketch (default `10`).
- Arduino IDE with built-in libraries:
  - `SD` (built-in)
  - `SPI` (built-in)

If your shield uses a different CS pin, edit `#define SD_CS_PIN 10` in `ArduinoSDLoader.ino`.

## Flash the Arduino Sketch

1. Open `utility/arduino-sd-loader/ArduinoSDLoader/ArduinoSDLoader.ino` in Arduino IDE.
2. Select your board and port.
3. Upload. The Serial Monitor at 115200 should print `OK SD_READY` if the SD initializes.

## Python Uploader

Install Python deps:

```bash
pip install -r utility/arduino-sd-loader/requirements.txt
```

Run the uploader (Windows example):

```bash
python utility/arduino-sd-loader/python_uploader.py --port COM3 --root tactile-comm-device/sd/SD_FUTURE_PROOF
```

- `--port` is your Arduino serial port (e.g., `COM3`, `/dev/ttyUSB0`).
- `--root` defaults to `tactile-comm-device/sd/SD_FUTURE_PROOF` if omitted.
- Add `--dry-run` to see actions without sending any data.

## Protocol (for reference)

Text commands terminated by `\n`:

- `PING` → `OK`
- `MKDIR <path>` → `OK` or `ERR`
- `LIST <path>` → `OK` then lines: `<name>,<D|F>,<size>` ... then `END`
- `EXISTS <path>` → `OK` if exists else `ERR NO`
- `DEL <path>` → `OK` or `ERR`
- `GET <path>` → first line: `<size>`, then raw bytes, then `OK`/`ERR`
- `PUT <path> <size>` → then send `<size>` raw bytes; device responds `OK`/`ERR`

Paths must start with `/` (SD root) and use forward slashes.

## Notes

- The uploader creates directories as needed and streams files in 64-byte chunks.
- For large transfers, ensure stable USB connection and adequate SD card quality.
- If initialization fails, verify CS pin and SD wiring; try a slower board or fresh FAT32 SD.
