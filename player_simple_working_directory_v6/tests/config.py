# tests/config.py
import os

SERIAL_PORT = os.getenv("TCD_SERIAL_PORT", "COM5")  # e.g. "COM5" on Windows or "/dev/ttyACM0" on Linux/Mac
BAUD = int(os.getenv("TCD_BAUD", "115200"))
READ_TIMEOUT = float(os.getenv("TCD_TIMEOUT", "3.5"))  # seconds
WRITE_CHUNK = 512

# Where to place on device
BANK = "HUMAN"          # or "GENERA~1" for generated
KEY = "SHIFT"           # must exist in /CONFIG/KEYS.CSV
FILENAME = "999.MP3"    # any valid 8.3 is fine

# Local sample file for upload
LOCAL_MP3 = os.getenv("TCD_LOCAL_MP3", "sample.mp3")  # path to a small mp3 you have locally
