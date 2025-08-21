# tests/test_01_handshake_status.py
import pytest
from .config import SERIAL_PORT, BAUD, READ_TIMEOUT
from .proto_utils import open_serial, enter_data_mode

def test_handshake_and_status_open_mode():
    ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
    try:
        enter_data_mode(ser)
        # Ask for STATUS, expect WRITES=ON and MODE=OPEN (from your recent change)
        ser.write(b"STATUS\n")
        seen = []
        for _ in range(8):
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if line:
                seen.append(line)
                if line.startswith("STATUS "):
                    assert "WRITES=ON" in line
                    assert "MODE=OPEN" in line  # requires your STATUS tweak
                    return
        raise AssertionError(f"STATUS not found or not OPEN mode; got {seen}")
    finally:
        ser.close()
