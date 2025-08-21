# tests/proto_utils.py
import time
import binascii
import serial

def crc32_file(path: str) -> int:
    crc = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def open_serial(port: str, baud: int, timeout: float) -> serial.Serial:
    ser = serial.Serial(port, baudrate=baud, timeout=timeout, write_timeout=timeout)
    time.sleep(0.1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

def read_line(ser: serial.Serial) -> str:
    """Reads one line (without trailing CR/LF). Returns '' on timeout."""
    raw = ser.readline()
    try:
        s = raw.decode("utf-8", errors="replace").strip()
    except Exception:
        s = ""
    return s

def write_line(ser: serial.Serial, line: str):
    ser.write((line + "\n").encode("utf-8"))
    ser.flush()

def enter_data_mode(ser: serial.Serial) -> None:
    # Standard handshake
    write_line(ser, "^DATA? v1")
    # Expect: DATA:OK v1
    for _ in range(5):
        resp = read_line(ser)
        if not resp:
            continue
        if resp.startswith("DATA:OK"):
            return
    raise AssertionError("Handshake failed: no 'DATA:OK' received")

def expect_prefix(ser: serial.Serial, prefix: str, tries: int = 20) -> str:
    """Read lines until one begins with prefix; returns that line or raises."""
    for _ in range(tries):
        s = read_line(ser)
        if s.startswith(prefix):
            return s
    raise AssertionError(f"Expected line starting with '{prefix}', but did not see it")
